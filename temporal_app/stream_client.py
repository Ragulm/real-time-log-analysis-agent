import os
import asyncio
from temporalio.client import Client

from agents.collector import LogCollector
from config import LOG_FILE_PATH
from temporal_app.workflow import LogWorkflow


async def connect_with_retry(address: str, retries: int = 20, delay: float = 2.0):
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
    print("📡 Watching logs and triggering Temporal workflows...")

    client = await connect_with_retry(os.getenv("TEMPORAL_ADDRESS", "localhost:7233"))

    collector = LogCollector(LOG_FILE_PATH)

    async for line in collector.tail_log():

        if "ERROR" in line or "CRITICAL" in line:
            print("🚨 Error detected → starting workflow")

            await client.start_workflow(
                LogWorkflow.run,
                line,
                id=f"log-{hash(line)}",
                task_queue="log-task-queue",
            )


if __name__ == "__main__":
    asyncio.run(main())
