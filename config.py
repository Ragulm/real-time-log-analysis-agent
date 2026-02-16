import os
import asyncio
from pathlib import Path
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel
from temporalio.client import Client

# ============================
# Base directory
# ============================

BASE_DIR = Path(__file__).parent

# Your app.log is in root folder
LOG_FILE_PATH = str(BASE_DIR / "app.log")

# Temporal settings
TEMPORAL_ADDRESS = os.getenv("TEMPORAL_ADDRESS", "localhost:7233")
TASK_QUEUE = os.getenv("TASK_QUEUE", "log-task-queue")

# ============================
# FastAPI app
# ============================

app = FastAPI(
    title="Real-Time Log Analysis Agent API",
    description="REST API to trigger Temporal workflows and power dashboard",
    version="2.0.0",
)

# ============================
# Global variables
# ============================

temporal_client = None
temporal_reconnect_task = None
simulated_results: dict[str, dict] = {}

# ============================
# Models
# ============================

class LogAnalysisRequest(BaseModel):
    log_line: str


class WorkflowResponse(BaseModel):
    workflow_id: str
    status: str
    message: str


# ============================
# Temporal connection
# ============================

async def connect_with_retry(address: str, retries: int = 5, delay: float = 2.0):

    for attempt in range(1, retries + 1):

        try:
            client = await Client.connect(address)
            print("✅ Connected to Temporal")
            return client

        except Exception as e:

            print(f"Temporal connection failed (attempt {attempt}): {e}")

            if attempt == retries:
                return None

            await asyncio.sleep(delay)


@app.on_event("startup")
async def startup():

    global temporal_client, temporal_reconnect_task

    print(f"Connecting to Temporal at {TEMPORAL_ADDRESS}")

    temporal_client = await connect_with_retry(TEMPORAL_ADDRESS)

    async def reconnect_loop():

        global temporal_client

        while temporal_client is None:

            try:
                temporal_client = await Client.connect(TEMPORAL_ADDRESS)
                print("✅ Reconnected to Temporal")

            except Exception as e:

                print(f"Reconnect failed: {e}")
                await asyncio.sleep(5)

    temporal_reconnect_task = asyncio.create_task(reconnect_loop())


@app.on_event("shutdown")
async def shutdown():

    global temporal_client

    if temporal_client:
        await temporal_client.close()
        print("Temporal client closed")


# ============================
# Health endpoint
# ============================

@app.get("/health")
async def health():

    return {
        "status": "healthy",
        "temporal_connected": temporal_client is not None
    }


# ============================
# Start workflow
# ============================

@app.post("/api/v1/analyze-log", response_model=WorkflowResponse)
async def analyze_log(request: LogAnalysisRequest):

    if not request.log_line.strip():
        raise HTTPException(400, "log_line empty")

    if not temporal_client:

        wid = f"local-{hash(request.log_line)}"

        simulated_results[wid] = {
            "workflow_id": wid,
            "status": "completed",
            "result": {
                "message": "Simulated result"
            }
        }

        return WorkflowResponse(
            workflow_id=wid,
            status="simulated",
            message="Temporal unavailable, simulated result"
        )

    try:

        from temporal_app.workflow import LogWorkflow

        workflow = await temporal_client.start_workflow(
            LogWorkflow.run,
            request.log_line,
            id=f"log-{hash(request.log_line)}",
            task_queue=TASK_QUEUE
        )

        return WorkflowResponse(
            workflow_id=workflow.id,
            status="started",
            message="Workflow started"
        )

    except Exception as e:

        raise HTTPException(500, str(e))


# ============================
# Get workflow result
# ============================

@app.get("/api/v1/workflow/{workflow_id}")
async def get_workflow(workflow_id: str):

    if not temporal_client:

        if workflow_id in simulated_results:
            return simulated_results[workflow_id]

        raise HTTPException(404, "Not found")

    try:

        handle = temporal_client.get_workflow_handle(workflow_id)
        result = await handle.result()

        return {
            "workflow_id": workflow_id,
            "status": "completed",
            "result": result
        }

    except Exception as e:

        return {
            "workflow_id": workflow_id,
            "status": "running",
            "message": str(e)
        }


# ============================
# List workflows
# ============================

@app.get("/api/v1/workflows")
async def list_workflows():

    if not temporal_client:
        return {"workflows": []}

    try:

        workflows = []

        async for wf in temporal_client.list_workflows():

            workflows.append({

                "id": wf.id,
                "run_id": wf.run_id,
                "status": wf.status.name,
                "start_time": str(wf.start_time),
                "close_time": str(wf.close_time) if wf.close_time else None
            })

        return {"workflows": workflows}

    except Exception as e:

        raise HTTPException(500, str(e))


# ============================
# Dashboard endpoint
# ============================

@app.get("/dashboard")
async def dashboard():

    path = BASE_DIR / "dashboard.html"

    if path.exists():
        return FileResponse(path)

    raise HTTPException(404, "dashboard.html not found")


# ============================
# Root endpoint
# ============================

@app.get("/")
async def root():

    return {
        "message": "Real-Time Log Analysis API",
        "dashboard": "/dashboard",
        "health": "/health",
        "workflows": "/api/v1/workflows",
        "log_file": LOG_FILE_PATH
    }


# ============================
# Run locally
# ============================

if __name__ == "__main__":

    import uvicorn

    uvicorn.run(
        "config:app",
        host="0.0.0.0",
        port=8080,
        reload=True
    )
