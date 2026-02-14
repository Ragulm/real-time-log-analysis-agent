import os
import asyncio
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
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


class LogAnalysisRequest(BaseModel):
    """Request payload to analyze a log line"""
    log_line: str


class WorkflowResponse(BaseModel):
    """Response from workflow trigger"""
    workflow_id: str
    status: str
    message: str


async def connect_with_retry(address: str, retries: int = 20, delay: float = 2.0):
    """Connect to Temporal server with retry logic"""
    for attempt in range(1, retries + 1):
        try:
            return await Client.connect(address)
        except Exception as exc:
            print(f"Temporal not ready ({exc}) — retry {attempt}/{retries} in {delay}s")
            if attempt == retries:
                raise
            await asyncio.sleep(delay)


@app.on_event("startup")
async def startup():
    """Initialize Temporal client on app startup"""
    global temporal_client
    temporal_address = os.getenv("TEMPORAL_ADDRESS", "localhost:7233")
    print(f"🔌 Connecting to Temporal at {temporal_address}...")
    temporal_client = await connect_with_retry(temporal_address)
    print("✅ Temporal client connected")


@app.on_event("shutdown")
async def shutdown():
    """Close Temporal client on app shutdown"""
    global temporal_client
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


@app.post("/api/v1/analyze-log", response_model=WorkflowResponse)
async def analyze_log(request: LogAnalysisRequest):
    """
    Trigger a Temporal workflow to analyze a log line.
    
    This endpoint accepts a log line and starts a workflow that:
    1. Analyzes the log for issues
    2. Explains the root cause using LLM
    3. Sends notifications
    
    Example:
    ```
    curl -X POST http://localhost:8000/api/v1/analyze-log \
      -H "Content-Type: application/json" \
      -d '{"log_line": "ERROR: Database connection timeout"}'
    ```
    """
    if not temporal_client:
        raise HTTPException(status_code=503, detail="Temporal service not available")
    
    if not request.log_line.strip():
        raise HTTPException(status_code=400, detail="log_line cannot be empty")
    
    try:
        from temporal_app.workflow import LogWorkflow
        
        # Start workflow
        workflow = await temporal_client.start_workflow(
            LogWorkflow.run,
            request.log_line,
            id=f"log-{hash(request.log_line)}",
            task_queue="log-task-queue",
        )
        
        return WorkflowResponse(
            workflow_id=workflow.id,
            status="started",
            message=f"Workflow started for log analysis: {request.log_line[:100]}...",
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start workflow: {str(e)}")


@app.get("/api/v1/workflow/{workflow_id}")
async def get_workflow_result(workflow_id: str):
    """
    Get the result of a completed workflow.
    
    Returns the analysis result if the workflow has finished.
    """
    if not temporal_client:
        raise HTTPException(status_code=503, detail="Temporal service not available")
    
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


@app.post("/api/v1/batch-analyze")
async def batch_analyze_logs(logs: list[str]):
    """
    Analyze multiple log lines in parallel.
    
    Starts workflows for each log line and returns workflow IDs.
    """
    if not temporal_client:
        raise HTTPException(status_code=503, detail="Temporal service not available")
    
    if not logs:
        raise HTTPException(status_code=400, detail="logs list cannot be empty")
    
    try:
        from temporal_app.workflow import LogWorkflow
        
        workflow_ids = []
        for log_line in logs:
            if log_line.strip():
                workflow = await temporal_client.start_workflow(
                    LogWorkflow.run,
                    log_line,
                    id=f"log-{hash(log_line)}",
                    task_queue="log-task-queue",
                )
                workflow_ids.append(workflow.id)
        
        return {
            "status": "submitted",
            "count": len(workflow_ids),
            "workflow_ids": workflow_ids,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start workflows: {str(e)}")


@app.get("/")
async def root():
    """API documentation endpoint"""
    return {
        "name": "Real-Time Log Analysis Agent API",
        "version": "1.0.0",
        "docs": "/docs",
        "dashboard": "/dashboard",
        "endpoints": [
            {"method": "GET", "path": "/health", "description": "Health check"},
            {"method": "GET", "path": "/dashboard", "description": "Interactive dashboard"},
            {"method": "POST", "path": "/api/v1/analyze-log", "description": "Start log analysis workflow"},
            {"method": "GET", "path": "/api/v1/workflow/{workflow_id}", "description": "Get workflow result"},
            {"method": "POST", "path": "/api/v1/batch-analyze", "description": "Analyze multiple logs"},
        ],
    }


@app.get("/dashboard")
async def get_dashboard():
    """Serve the interactive dashboard"""
    dashboard_path = Path(__file__).parent / "dashboard.html"
    if dashboard_path.exists():
        return FileResponse(dashboard_path, media_type="text/html")
    else:
        raise HTTPException(status_code=404, detail="Dashboard not found")


if __name__ == "__main__":
    import uvicorn
    
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
