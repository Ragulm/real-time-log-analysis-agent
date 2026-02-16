from temporalio import activity
from agents.analyzer import IssueAnalyzer
from agents.explainer import IssueExplainer
from agents.notifier import EmailNotifier


@activity.defn
async def analyzer_activity(log_line: str):
    """
    Analyze a log line to determine if it represents an issue.
    Always returns a valid dict to prevent workflow failures.
    """
    try:
        activity.logger.info(f"Starting analyzer activity for: {log_line[:80]}")
        analyzer = IssueAnalyzer()
        result = await analyzer.analyze_log(log_line)

        # Ensure result is always a dict
        if result is None:
            activity.logger.warning("Analyzer returned None, returning safe default")
            return {
                "is_issue": False,
                "issue_type": "unknown",
                "explanation": "Analyzer returned no result"
            }

        # Ensure result is dict
        if not isinstance(result, dict):
            activity.logger.error(f"Analyzer returned non-dict type: {type(result)}")
            return {
                "is_issue": False,
                "issue_type": "invalid",
                "explanation": "Analyzer returned invalid format"
            }

        # Validate required keys
        if "is_issue" not in result:
            result["is_issue"] = False
        if "issue_type" not in result:
            result["issue_type"] = "unknown"
        if "explanation" not in result:
            result["explanation"] = "No explanation provided"

        activity.logger.info(f"Analyzer activity completed: is_issue={result.get('is_issue')}")
        return result

    except Exception as e:
        activity.logger.error(f"Analyzer activity exception: {type(e).__name__}: {e}")
        return {
            "is_issue": False,
            "issue_type": "analyzer_error",
            "explanation": f"Analyzer failed: {str(e)[:100]}"
        }


@activity.defn
async def explainer_activity(log_line: str, analysis: dict):
    """
    Generate a detailed explanation for a detected issue.
    Returns a string explanation or error message.
    """
    try:
        activity.logger.info(f"Starting explainer activity for issue type: {analysis.get('issue_type')}")
        
        if not isinstance(analysis, dict):
            activity.logger.warning("Analysis is not a dict, skipping explanation")
            return "Invalid analysis format provided to explainer"
        
        explainer = IssueExplainer()
        result = await explainer.explain_issue(log_line, analysis)

        if result is None:
            activity.logger.warning("Explainer returned None")
            return "No explanation generated"

        activity.logger.info("Explainer activity completed")
        return result

    except Exception as e:
        activity.logger.error(f"Explainer activity exception: {type(e).__name__}: {e}")
        return f"Explanation failed: {str(e)[:200]}"


@activity.defn
async def notifier_activity(issue_type: str, explanation: str, log_line: str):
    """
    Send notification (email) about detected issue.
    Returns status string. Non-critical - failures don't fail the workflow.
    """
    try:
        activity.logger.info(f"Starting notifier activity for issue type: {issue_type}")
        
        notifier = EmailNotifier()
        await notifier.send_email(issue_type, explanation, log_line)
        
        activity.logger.info("Notifier activity completed")
        return "Email sent successfully"

    except Exception as e:
        activity.logger.warning(f"Notifier activity exception (non-critical): {type(e).__name__}: {e}")
        return f"Email failed: {str(e)[:200]}"

