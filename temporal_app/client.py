import asyncio
from temporalio.client import Client
from temporal_app.workflow import LogWorkflow


async def main():
    client = await Client.connect("localhost:7233")

    log_line = "CRITICAL FAILURE: Database connection timeout"

    result = await client.execute_workflow(
        LogWorkflow.run,
        log_line,
        id="log-workflow-1",
        task_queue="log-task-queue",
    )

    print("RESULT:", result)


if __name__ == "__main__":
    asyncio.run(main())
