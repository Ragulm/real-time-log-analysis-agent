from temporalio import activity
from agents.analyzer import IssueAnalyzer
from agents.explainer import IssueExplainer
from agents.notifier import EmailNotifier


@activity.defn
async def analyzer_activity(log_line: str):
    analyzer = IssueAnalyzer()
    return await analyzer.analyze_log(log_line)


@activity.defn
async def explainer_activity(log_line: str, analysis: dict):
    explainer = IssueExplainer()
    return await explainer.explain_issue(log_line, analysis)


@activity.defn
async def notifier_activity(issue_type: str, explanation: str, log_line: str):
    notifier = EmailNotifier()
    await notifier.send_email(issue_type, explanation, log_line)
