import os
import asyncio
import uuid
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from pathlib import Path
from pydantic import BaseModel
from temporalio.client import Client


app = FastAPI(
    title="Real-Time Log Analysis Agent API",
    description="REST API to trigger Temporal workflows for log analysis",
    version="1.0.0",
)


# Global Temporal client
temporal_client = None

# Background reconnect task (tries to reconnect if Temporal unavailable)
temporal_reconnect_task = None

# In-memory simulated results when Temporal is unavailable
simulated_results: dict[str, dict] = {}


class LogAnalysisRequest(BaseModel):
    """Request payload to analyze a log line"""
    log_line: str


class WorkflowResponse(BaseModel):
    """Response from workflow trigger"""
    workflow_id: str
    status: str
    message: str


async def connect_with_retry(address: str, retries: int = 3, delay: float = 1.0):
    """Connect to Temporal server with retry logic (non-blocking)"""
    for attempt in range(1, retries + 1):
        try:
            return await Client.connect(address)
        except Exception as exc:
            print(f"Temporal not ready ({exc}) — retry {attempt}/{retries} in {delay}s")
            if attempt == retries:
                print(f"⚠️ Could not connect to Temporal at {address}. API will work but workflows won't execute.")
                return None
            await asyncio.sleep(delay)


@app.on_event("startup")
async def startup():
    """Initialize Temporal client on app startup and start background reconnect if needed"""
    global temporal_client, temporal_reconnect_task

    temporal_address = os.getenv("TEMPORAL_ADDRESS", "localhost:7233")
    print(f"🔌 Connecting to Temporal at {temporal_address}...")

    try:
        temporal_client = await connect_with_retry(temporal_address)

        if temporal_client:
            print("✅ Temporal client connected")

        else:
            print("⚠️ Temporal client not available — starting background reconnect loop")

            async def _reconnect_loop(address: str, interval: float = 10.0):
                global temporal_client

                while temporal_client is None:
                    try:
                        client = await Client.connect(address)
                        temporal_client = client
                        print("✅ Temporal client connected (reconnected in background)")
                        return
                    except Exception as exc:
                        print(f"Temporal reconnect failed ({exc}) — retrying in {interval}s")
                        await asyncio.sleep(interval)

            temporal_reconnect_task = asyncio.create_task(_reconnect_loop(temporal_address))

    except Exception as e:
        print(f"⚠️ Temporal connection failed on startup: {e}. Continuing with background reconnect if needed.")

        if temporal_reconnect_task is None:

            async def _reconnect_loop(address: str, interval: float = 10.0):
                global temporal_client

                while temporal_client is None:
                    try:
                        client = await Client.connect(address)
                        temporal_client = client
                        print("✅ Temporal client connected (reconnected in background)")
                        return
                    except Exception as exc:
                        print(f"Temporal reconnect failed ({exc}) — retrying in {interval}s")
                        await asyncio.sleep(interval)

            temporal_reconnect_task = asyncio.create_task(_reconnect_loop(temporal_address))


@app.on_event("shutdown")
async def shutdown():
    """Close Temporal client and cancel background reconnect task on shutdown"""
    global temporal_client, temporal_reconnect_task

    if temporal_reconnect_task:
        temporal_reconnect_task.cancel()
        try:
            await temporal_reconnect_task
        except asyncio.CancelledError:
            pass

    if temporal_client:
        await temporal_client.close()
        print("❌ Temporal client closed")


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "temporal_connected": temporal_client is not None,
    }


@app.get("/diag")
async def diagnostic_check():
    """Diagnostic endpoint: DNS + HTTPS probe for Groq plus env info (does not reveal secrets)."""
    import socket
    import urllib.request
    import asyncio

    loop = asyncio.get_running_loop()

    def _dns_lookup():
        return socket.getaddrinfo("api.groq.com", 443)

    def _https_probe():
        req = urllib.request.Request("https://api.groq.com/", method="GET")
        with urllib.request.urlopen(req, timeout=5) as resp:
            return resp.getcode()

    out = {
        "temporal_address": os.getenv("TEMPORAL_ADDRESS", ""),
        "temporal_connected": temporal_client is not None,
        "wait_for_temporal": os.getenv("WAIT_FOR_TEMPORAL", ""),
        "groq_api_key_present": bool(os.getenv("GROQ_API_KEY")),
    }

    # DNS lookup (run in executor to avoid blocking event loop)
    try:
        addrs = await loop.run_in_executor(None, _dns_lookup)
        ips = sorted({a[4][0] for a in addrs})
        out["dns_ok"] = True
        out["dns_addresses"] = ips
    except Exception as e:
        out["dns_ok"] = False
        out["dns_error"] = str(e)

    # HTTPS probe
    try:
        status = await loop.run_in_executor(None, _https_probe)
        out["https_ok"] = True
        out["https_status"] = status
    except Exception as e:
        out["https_ok"] = False
        out["https_error"] = str(e)

    return out


@app.get("/diag/groq-test")
async def groq_authenticated_test():
    """Performs a minimal authenticated Groq SDK call (does NOT expose the key).

    Returns: { ok: bool, detail: str }
    """
    import os
    try:
        from groq import AsyncGroq
    except Exception:
        return {"ok": False, "error": "groq SDK not installed in container"}

    if not os.getenv("GROQ_API_KEY"):
        return {"ok": False, "error": "GROQ_API_KEY not set in environment"}

    _key = os.getenv("GROQ_API_KEY")
    if _key is not None:
        _key = _key.strip()
    client = AsyncGroq(api_key=_key)

    try:
        # Small, cheap request to verify auth & connectivity
        resp = await client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {"role": "system", "content": "You are a short health-check responder."},
                {"role": "user", "content": "Reply with the single word: pong"},
            ],
            temperature=0,
            max_tokens=3,
        )

        content = None
        try:
            content = resp.choices[0].message.content.strip()
        except Exception:
            content = str(resp)[:200]

        return {"ok": True, "content_preview": content}

    except Exception as e:
        # Return a sanitized error (no secrets)
        msg = str(e)
        if "403" in msg or "Forbidden" in msg:
            reason = "auth_or_permission_error"
        else:
            reason = "other_error"
        return {"ok": False, "error": reason, "detail": msg[:800]}


@app.get("/health/groq")
async def health_groq_probe():
    """Cloud Run-friendly health probe that verifies Groq SDK auth & connectivity.

    Returns 200 when Groq responds quickly with the expected `pong` reply;
    returns 503 on timeout, SDK missing, or authentication/connectivity failures.
    """
    import os

    # Quick checks without exposing secrets
    try:
        from groq import AsyncGroq
    except Exception:
        return JSONResponse(status_code=503, content={"ok": False, "error": "groq SDK not installed"})

    if not os.getenv("GROQ_API_KEY"):
        return JSONResponse(status_code=503, content={"ok": False, "error": "GROQ_API_KEY not set"})

    _key = os.getenv("GROQ_API_KEY")
    if _key is not None:
        _key = _key.strip()

    client = AsyncGroq(api_key=_key)

    try:
        # Keep probe short so Cloud Run health checks are fast and deterministic
        resp = await asyncio.wait_for(
            client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=[
                    {"role": "system", "content": "health-check responder"},
                    {"role": "user", "content": "pong"},
                ],
                temperature=0,
                max_tokens=1,
            ),
            timeout=3.0,
        )

        content = None
        try:
            content = resp.choices[0].message.content.strip()
        except Exception:
            content = str(resp)[:100]

        if content and content.lower().startswith("pong"):
            return JSONResponse(status_code=200, content={"ok": True, "content_preview": content})

        return JSONResponse(status_code=503, content={"ok": False, "content_preview": content})

    except asyncio.TimeoutError:
        return JSONResponse(status_code=503, content={"ok": False, "error": "timeout"})
    except Exception as e:
        return JSONResponse(status_code=503, content={"ok": False, "error": str(e)[:200]})


@app.post("/api/v1/analyze-log", response_model=WorkflowResponse)
async def analyze_log(request: LogAnalysisRequest):
    """
    Trigger a Temporal workflow to analyze a log line.
    """

    if not request.log_line.strip():
        raise HTTPException(status_code=400, detail="log_line cannot be empty")

    # Simulation if Temporal unavailable
    if not temporal_client:

        line = request.log_line.lower()

        if "disk" in line or "space" in line:
            category = "disk_space"
            explanation = "Disk space critically low — free up space or extend volume."

        elif "database" in line or "db" in line or "connection" in line:
            category = "database"
            explanation = "Database connection issues — check DB server and network."

        elif "nullpointer" in line or "null" in line:
            category = "exception"
            explanation = "Unhandled exception in application code."

        else:
            category = "unknown"
            explanation = "Automatically generated analysis."

        wid = f"local-{abs(hash(request.log_line))}-{int(asyncio.get_event_loop().time())}"

        simulated_results[wid] = {
            "workflow_id": wid,
            "status": "completed",
            "result": {
                "category": category,
                "explanation": explanation,
                "input": request.log_line,
            },
        }

        return WorkflowResponse(
            workflow_id=wid,
            status="simulated",
            message="Simulated analysis completed",
        )

    try:
        from temporal_app.workflow import LogWorkflow

        workflow = await temporal_client.start_workflow(
            LogWorkflow.run,
            request.log_line,
            id=f"log-{uuid.uuid4().hex}",
            task_queue="log-task-queue",
        )

        return WorkflowResponse(
            workflow_id=workflow.id,
            status="started",
            message="Workflow started",
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/workflow/{workflow_id}")
async def get_workflow_result(workflow_id: str):

    if not temporal_client:

        if workflow_id in simulated_results:
            return simulated_results[workflow_id]

        raise HTTPException(status_code=404, detail="Workflow result not found")

    try:
        workflow_handle = temporal_client.get_workflow_handle(workflow_id)
        result = await workflow_handle.result()

        return {
            "workflow_id": workflow_id,
            "status": "completed",
            "result": result,
        }

    except Exception as e:
        return {
            "workflow_id": workflow_id,
            "status": "error",
            "message": str(e),
        }


@app.get("/api/v1/workflows")
async def get_workflows_stats():
    """
    Get workflow statistics from Temporal.
    Returns: list of recent workflows and statistics
    """
    if not temporal_client:
        # Return empty if Temporal not available
        return {
            "workflows": [],
            "stats": {
                "total": 0,
                "completed": 0,
                "running": 0,
                "errors": 0,
            },
            "categories": {},
        }

    try:
        from temporalio.api.workflowservice.v1 import ListWorkflowExecutionsRequest
        from temporalio.api.enums.v1 import WorkflowExecutionStatus
        from google.protobuf.timestamp_pb2 import Timestamp
        
        # Query for recent workflows
        workflows = []
        stats = {
            "total": 0,
            "completed": 0,
            "running": 0,
            "errors": 0,
        }
        categories = {}
        
        # Try to list workflows from Temporal
        try:
            # List all workflows from the default namespace
            async for execution in await temporal_client.list_workflows("WorkflowType = 'LogWorkflow'"):
                workflow_id = execution.execution.workflow_id
                status_name = execution.status.name if hasattr(execution.status, 'name') else str(execution.status)
                
                # Map status
                if execution.status == 2:  # COMPLETED
                    status = "completed"
                    stats["completed"] += 1
                elif execution.status == 1:  # RUNNING
                    status = "running"  
                    stats["running"] += 1
                else:
                    status = "error"
                    stats["errors"] += 1
                
                stats["total"] += 1
                
                # Try to get result
                try:
                    workflow_handle = temporal_client.get_workflow_handle(workflow_id)
                    result = None
                    try:
                        result = await asyncio.wait_for(workflow_handle.result(), timeout=1.0)
                    except asyncio.TimeoutError:
                        result = None
                    
                    category = "unknown"
                    if result and isinstance(result, dict):
                        category = result.get("category", "unknown")
                    
                    categories[category] = categories.get(category, 0) + 1
                    
                    workflows.append({
                        "id": workflow_id,
                        "status": status,
                        "category": category,
                        "timestamp": int(execution.execution.start_time.timestamp() * 1000) if execution.execution.start_time else None,
                    })
                except Exception as e:
                    print(f"Could not fetch result for {workflow_id}: {e}")
                    workflows.append({
                        "id": workflow_id,
                        "status": status,
                        "category": "unknown",
                        "timestamp": int(execution.execution.start_time.timestamp() * 1000) if execution.execution.start_time else None,
                    })
        except Exception as e:
            print(f"Error listing workflows from Temporal: {e}")
            # Return empty list if query fails
            pass
        
        return {
            "workflows": workflows[-100:],  # Return last 100 workflows
            "stats": stats,
            "categories": categories,
        }
        
    except Exception as e:
        print(f"Error getting workflow stats: {e}")
        return {
            "workflows": [],
            "stats": {
                "total": 0,
                "completed": 0,
                "running": 0,
                "errors": 0,
            },
            "categories": {},
        }


@app.get("/dashboard")
async def get_dashboard():

    dashboard_path = Path(__file__).parent / "dashboard.html"

    if dashboard_path.exists():
        return FileResponse(dashboard_path)

    raise HTTPException(status_code=404, detail="Dashboard not found")


if __name__ == "__main__":

    import uvicorn

    port = int(os.getenv("PORT", 8080))

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=port,
    )
