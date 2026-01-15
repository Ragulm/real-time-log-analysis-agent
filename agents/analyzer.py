import json
from groq import AsyncGroq
import os

class IssueAnalyzer:
    def __init__(self):
        self.client = AsyncGroq(api_key=os.getenv("GROQ_API_KEY"))

    async def analyze_log(self, log_line):
        """
        Analyzes a single log line to determine if it is an issue.
        """
        # Quick heuristic filter to save API calls (optional but good for speed)
        # For this demo, let's send 'ERROR' logs to LLM to verify severity.
        if "ERROR" not in log_line and "CRITICAL" not in log_line:
            return None

        print(f"Agent 2 (Analyzer): Analyzing potential issue: {log_line[:50]}...")

        prompt = f"""
        Analyze this log entry. valid JSON output only.
        Is this a critical technical issue requiring intervention?
        
        Log Entry: "{log_line}"
        
        Output format:
        {{
            "is_issue": boolean,
            "severity": "low" | "medium" | "high",
            "issue_type": "string"
        }}
        """

        try:
            chat_completion = await self.client.chat.completions.create(
                messages=[
                    {
                        "role": "system",
                        "content": "You are a robust log analysis agent. Return ONLY JSON.",
                    },
                    {
                        "role": "user",
                        "content": prompt,
                    }
                ],
                model="llama3-70b-8192",
                temperature=0,
                response_format={"type": "json_object"},
            )
            
            result = json.loads(chat_completion.choices[0].message.content)
            
            if result.get("is_issue"):
                return result
            return None

        except Exception as e:
            print(f"Agent 2 Error: {e}")
            return None
