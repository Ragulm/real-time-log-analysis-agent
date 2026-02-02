import asyncio
from temporalio.client import Client

from agents.collector import LogCollector
from config import LOG_FILE_PATH
from temporal_app.workflow import LogWorkflow


async def main():
    print("📡 Watching logs and triggering Temporal workflows...")

    client = await Client.connect("localhost:7233")

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
