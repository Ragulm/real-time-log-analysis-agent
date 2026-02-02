from dotenv import load_dotenv
load_dotenv()

import asyncio
from temporalio.client import Client
from temporalio.worker import Worker

from temporal_app.workflow import LogWorkflow
from temporal_app.activities import (
    analyzer_activity,
    explainer_activity,
    notifier_activity,
)


async def main():
    client = await Client.connect("localhost:7233")

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
