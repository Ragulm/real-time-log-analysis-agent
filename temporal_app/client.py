import os
import asyncio
from temporalio.client import Client
from temporal_app.workflow import LogWorkflow

TEMPORAL_ADDRESS = os.getenv("TEMPORAL_ADDRESS", "localhost:7233")


async def connect_with_retry(address: str, retries: int = 10, delay: float = 2.0):
    import asyncio
    for attempt in range(1, retries + 1):
        try:
            return await Client.connect(address)
        except Exception as exc:
            print(f"Temporal not ready ({exc}) — retry {attempt}/{retries} in {delay}s")
            if attempt == retries:
                raise
            await asyncio.sleep(delay)


async def main():
    client = await connect_with_retry(TEMPORAL_ADDRESS)

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
