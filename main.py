import asyncio
import os
import operator
from typing import TypedDict, Annotated, Optional
from dotenv import load_dotenv

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from langgraph.graph import StateGraph, END
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field

from agents.collector import LogCollector
from config import LOG_FILE_PATH, GROQ_API_KEY

load_dotenv()

# --- State Definition ---
class AgentState(TypedDict):
    log_line: str
    is_issue: bool
    severity: Optional[str]
    issue_type: Optional[str]
    explanation: Optional[str]

# --- LLM Setup ---
llm_small = ChatGroq(temperature=0, model_name="llama-3.1-8b-instant", groq_api_key=GROQ_API_KEY)
llm_large = ChatGroq(temperature=0.5, model_name="llama-3.3-70b-versatile", groq_api_key=GROQ_API_KEY)

# --- Analysis Logic ---
class AnalysisResult(BaseModel):
    is_issue: bool = Field(description="True if the log indicates an error or critical issue")
    severity: Optional[str] = Field(description="low, medium, or high")
    issue_type: Optional[str] = Field(description="Short description of the issue type")

async def analyzer_node(state: AgentState):
    log_line = state["log_line"]
    
    # Simple pre-filter pattern matching to save tokens
    if "ERROR" not in log_line and "CRITICAL" not in log_line:
        return {"is_issue": False, "severity": None, "issue_type": None}

    print(f"Agent 2 (Analyzer): Checking: {log_line[:40]}...")
    
    structured_llm = llm_small.with_structured_output(AnalysisResult)
    prompt = ChatPromptTemplate.from_messages([
        ("system", "You are a robust log analysis agent. Analyze the log entry."),
        ("user", "Log Entry: {log_line}")
    ])
    chain = prompt | structured_llm
    
    try:
        result = await chain.ainvoke({"log_line": log_line})
        return {
            "is_issue": result.is_issue,
            "severity": result.severity,
            "issue_type": result.issue_type
        }
    except Exception as e:
        print(f"Analyzer Error: {e}")
        return {"is_issue": False}

# --- Explanation Logic ---
async def explainer_node(state: AgentState):
    print(f"Agent 3 (Explainer): Generating fix for {state['issue_type']}...")
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", "You are a helpful SRE assistant. Explain the technical issue and suggest a fix."),
        ("user", "Log: {log_line}\nContext: {issue_type} (Severity: {severity})\n\nProvide a concise explanation.")
    ])
    chain = prompt | llm_large
    
    result = await chain.ainvoke({
        "log_line": state["log_line"],
        "issue_type": state["issue_type"],
        "severity": state["severity"]
    })
    
    return {"explanation": result.content}

# --- Notification Logic ---
async def notifier_node(state: AgentState):
    print(f"Agent 4 (Notifier): Sending email alert...")
    
    sender_email = os.getenv("SENDER_EMAIL")
    sender_password = os.getenv("SENDER_PASSWORD")
    recipient_email = os.getenv("RECIPIENT_EMAIL")
    smtp_server = os.getenv("SMTP_SERVER")
    smtp_port = os.getenv("SMTP_PORT")

    if not all([sender_email, sender_password, recipient_email, smtp_server, smtp_port]):
        print("Skipping real email: SMTP configuration missing in .env")
        print(f"[PREVIEW] Subject: {state['severity'].upper()} Alert: {state['issue_type']}")
        return {}

    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = recipient_email
    msg['Subject'] = f"{state['severity'].upper()} Alert: {state['issue_type']}"
    
    body = f"Technical Issue Detected:\n\n{state['explanation']}\n\nOriginal Log:\n{state['log_line']}"
    msg.attach(MIMEText(body, 'plain'))

    try:
        # Run synchronous SMTP code in a thread to avoid blocking the loop
        def send():
            with smtplib.SMTP(smtp_server, int(smtp_port)) as server:
                server.starttls()
                server.login(sender_email, sender_password)
                server.send_message(msg)
        
        await asyncio.to_thread(send)
        print(f"[EMAIL SENT] To: {recipient_email}")
        
    except Exception as e:
        print(f"Failed to send email: {e}")

    return {}

# --- Conditional Edge ---
def should_continue(state: AgentState):
    if state["is_issue"]:
        return "explainer"
    return END

# --- Graph Construction ---
workflow = StateGraph(AgentState)

workflow.add_node("analyzer", analyzer_node)
workflow.add_node("explainer", explainer_node)
workflow.add_node("notifier", notifier_node)

workflow.set_entry_point("analyzer")

workflow.add_conditional_edges(
    "analyzer",
    should_continue,
    {
        "explainer": "explainer",
        END: END
    }
)

workflow.add_edge("explainer", "notifier")
workflow.add_edge("notifier", END)

app = workflow.compile()

# --- Main Driver ---
async def main():
    print("Initializing LangGraph Multi-Agent System...")
    collector = LogCollector(LOG_FILE_PATH)

    async for line in collector.tail_log():
        # Invoke the graph for each log line
        # We start with basic state
        initial_state = {"log_line": line, "is_issue": False, "severity": None, "issue_type": None, "explanation": None}
        
        # We use ainvoke to run the graph asynchronously
        # The graph handles the flow based on the result of the analyzer
        await app.ainvoke(initial_state)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nSystem stopped.")
