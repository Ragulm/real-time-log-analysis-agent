from dotenv import load_dotenv
load_dotenv()

import os
import asyncio
from temporalio.client import Client
from temporalio.worker import Worker

from temporal_app.workflow import LogWorkflow
from temporal_app.activities import (
    analyzer_activity,
    explainer_activity,
    notifier_activity,
)


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
    client = await connect_with_retry(os.getenv("TEMPORAL_ADDRESS", "localhost:7233"))

    worker = Worker(
        client,
        task_queue="log-task-queue",
        workflows=[LogWorkflow],
        activities=[
            analyzer_activity,
            explainer_activity,
            notifier_activity,
        ],
    )

    print("✅ Temporal worker started")
    await worker.run()


if __name__ == "__main__":
    asyncio.run(main())
