from datetime import timedelta
from temporalio import workflow
from temporalio.common import RetryPolicy

from temporal_app.activities import (
    analyzer_activity,
    explainer_activity,
    notifier_activity,
)


@workflow.defn
class LogWorkflow:

    @workflow.run
    async def run(self, log_line: str):

        # -----------------------------
        # Retry Policy (shared)
        # -----------------------------
        retry_policy = RetryPolicy(
            initial_interval=timedelta(seconds=5),
            backoff_coefficient=2.0,
            maximum_interval=timedelta(seconds=60),
            maximum_attempts=3,
        )

        # -----------------------------
        # Analyzer
        # -----------------------------
        analysis = await workflow.execute_activity(
            analyzer_activity,
            log_line,
            start_to_close_timeout=timedelta(seconds=30),
            retry_policy=retry_policy,
        )

        if not analysis.get("is_issue"):
            return "No issue detected"

        # -----------------------------
        # Explainer
        # -----------------------------
        explanation = await workflow.execute_activity(
            explainer_activity,
            args=[log_line, analysis],
            start_to_close_timeout=timedelta(seconds=60),
            retry_policy=retry_policy,
        )

        # -----------------------------
        # Notifier (no retry)
        # -----------------------------
        await workflow.execute_activity(
            notifier_activity,
            args=[
                analysis["issue_type"],
                explanation,
                log_line,
            ],
            start_to_close_timeout=timedelta(seconds=30),
        )

        return "Alert processed successfully"
