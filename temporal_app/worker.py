from dotenv import load_dotenv
load_dotenv()

import os
import asyncio
import logging
from temporalio.client import Client
from temporalio.worker import Worker

from temporal_app.workflow import LogWorkflow
from temporal_app.activities import (
    analyzer_activity,
    explainer_activity,
    notifier_activity,
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s %(name)s: %(message)s'
)
logger = logging.getLogger(__name__)


async def connect_with_retry(address: str, retries: int = 10, delay: float = 3.0):
    """
    Connect to Temporal with exponential backoff retry logic.
    """
    for attempt in range(1, retries + 1):
        try:
            logger.info(f"Connecting to Temporal at {address}...")
            client = await Client.connect(address)
            logger.info("✅ Connected to Temporal successfully")
            return client
        except Exception as exc:
            logger.warning(f"⚠️  Temporal not ready (attempt {attempt}/{retries}): {exc}")
            if attempt == retries:
                logger.error(f"Failed to connect to Temporal after {retries} attempts. Worker will not start.")
                return None
            # Exponential backoff with jitter
            wait_time = min(delay * (attempt ** 0.5), 30)
            logger.info(f"Retrying in {wait_time:.1f}s...")
            await asyncio.sleep(wait_time)


async def main():
    temporal_address = os.getenv("TEMPORAL_ADDRESS", "localhost:7233")
    logger.info(f"Container starting with ROLE=worker")
    logger.info(f"PORT={os.getenv('PORT', '8080')}")
    logger.info(f"WAIT_FOR_TEMPORAL={os.getenv('WAIT_FOR_TEMPORAL', 'true')}")
    logger.info(f"🔄 Starting HTTP health server and Temporal worker")
    
    # Connect to Temporal
    logger.info(f"Waiting for Temporal at {temporal_address}...")
    client = await connect_with_retry(temporal_address)
    
    if not client:
        logger.error("Could not connect to Temporal. Worker will not start.")
        logger.info("Container will remain running for debugging. Check logs above.")
        # Keep the process alive
        try:
            while True:
                await asyncio.sleep(300)
        except KeyboardInterrupt:
            logger.info("Worker shutdown requested")
        return

    logger.info("Temporal reachable")
    logger.info("Starting Temporal worker...")

    # Define workflows and activities
    _workflows = [LogWorkflow]
    _activities = [
        analyzer_activity,
        explainer_activity,
        notifier_activity,
    ]

    # Log what we're registering
    logger.info("📋 Registering worker with:")
    logger.info(f"  task_queue = 'log-task-queue'")
    try:
        workflow_names = [w.__name__ for w in _workflows]
        logger.info(f"  workflows = {workflow_names}")
    except Exception as e:
        logger.warning(f"  workflows = [<unable to list: {e}>]")
    try:
        activity_names = [a.__name__ for a in _activities]
        logger.info(f"  activities = {activity_names}")
    except Exception as e:
        logger.warning(f"  activities = [<unable to list: {e}>]")

    # Create and run worker
    try:
        worker = Worker(
            client,
            task_queue="log-task-queue",
            workflows=_workflows,
            activities=_activities,
        )

        logger.info("✅ Temporal worker started and listening for tasks")
        await worker.run()
    except KeyboardInterrupt:
        logger.info("Worker shutdown requested")
    except Exception as e:
        logger.error(f"Worker error: {type(e).__name__}: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    asyncio.run(main())

