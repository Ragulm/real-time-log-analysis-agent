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

        workflow.logger.info(f"Workflow started for log: {log_line}")

        # Analyzer retry policy - longer timeouts to account for LLM API latency
        analyzer_retry_policy = RetryPolicy(
            initial_interval=timedelta(seconds=3),
            backoff_coefficient=2.0,
            maximum_interval=timedelta(seconds=45),
            maximum_attempts=2,  # Reduced to avoid cascading failures
        )

        # Explainer and notifier retry policy - more lenient
        standard_retry_policy = RetryPolicy(
            initial_interval=timedelta(seconds=2),
            backoff_coefficient=1.5,
            maximum_interval=timedelta(seconds=30),
            maximum_attempts=2,
        )

        # Analyzer activity - increased timeout to allow Groq API calls
        # IMPORTANT: activity timeout must be > call timeout + buffer
        try:
            analysis = await workflow.execute_activity(
                analyzer_activity,
                log_line,
                start_to_close_timeout=timedelta(seconds=90),  # Increased from 60
                retry_policy=analyzer_retry_policy,
            )
        except Exception as e:
            workflow.logger.error(f"Analyzer activity failed: {e}")
            return {
                "status": "analyzer_failed",
                "error": str(e),
                "log_line": log_line
            }

        workflow.logger.info(f"Analysis result: {analysis}")

        # SAFE CHECK - Validate analysis result
        if not analysis or not isinstance(analysis, dict):
            workflow.logger.warning("Analyzer returned invalid result")
            return {
                "status": "invalid_analysis",
                "analysis": analysis,
                "log_line": log_line
            }

        if not analysis.get("is_issue"):
            workflow.logger.info("No issue detected in log")
            return {
                "status": "no_issue",
                "analysis": analysis,
                "log_line": log_line
            }

        # Explainer activity
        try:
            explanation = await workflow.execute_activity(
                explainer_activity,
                args=[log_line, analysis],
                start_to_close_timeout=timedelta(seconds=90),  # Increased from 60
                retry_policy=standard_retry_policy,
            )
        except Exception as e:
            workflow.logger.error(f"Explainer activity failed: {e}")
            explanation = f"Explanation failed: {str(e)}"

        workflow.logger.info(f"Explanation result: {explanation}")

        # Notifier activity - no retry, best effort
        try:
            notification = await workflow.execute_activity(
                notifier_activity,
                args=[
                    analysis.get("issue_type", "unknown"),
                    explanation,
                    log_line,
                ],
                start_to_close_timeout=timedelta(seconds=60),  # Increased from 30
                retry_policy=standard_retry_policy,
            )
            workflow.logger.info(f"Notification result: {notification}")
        except Exception as e:
            workflow.logger.warning(f"Notifier activity failed (non-critical): {e}")

        workflow.logger.info("Workflow completed")

        return {
            "status": "completed",
            "analysis": analysis,
            "explanation": explanation
        }
