import json
import os
import asyncio
from groq import AsyncGroq


class IssueAnalyzer:

    def __init__(self):
        # strip whitespace/newlines from secret to avoid illegal header values
        _key = os.getenv("GROQ_API_KEY")
        if _key is not None:
            _key = _key.strip()
        self.client = AsyncGroq(api_key=_key)

        # Per-call timeout (seconds) and local retry attempts
        try:
            self._call_timeout = float(os.getenv("GROQ_CALL_TIMEOUT", "25"))
        except Exception:
            self._call_timeout = 25.0

        try:
            self._call_retries = int(os.getenv("GROQ_CALL_RETRIES", "1"))
        except Exception:
            self._call_retries = 1

    async def analyze_log(self, log_line):

        print(f"Analyzer received log: {log_line}")

        # Optional fast filter
        if "ERROR" not in log_line.upper() and "CRITICAL" not in log_line.upper():
            return {
                "is_issue": False,
                "issue_type": "non_error_log",
                "explanation": "Log does not contain ERROR or CRITICAL keywords"
            }

        prompt = f"""Analyze this log entry and determine if it is a real issue.

Log Entry:
{log_line}

Return ONLY valid JSON (no markdown, no code blocks):

{{
  "is_issue": true or false,
  "issue_type": "short issue type",
  "explanation": "short explanation"
}}"""

        last_exc = None
        for attempt in range(1, self._call_retries + 2):
            try:
                print(f"Analyzer: Attempt {attempt}/{self._call_retries + 1} to call Groq API")
                
                # Create the coroutine
                coro = self.client.chat.completions.create(
                    model="llama-3.1-8b-instant",
                    messages=[
                        {"role": "system", "content": "You are a log analysis AI. Return ONLY valid JSON, no markdown."},
                        {"role": "user", "content": prompt},
                    ],
                    temperature=0,
                    timeout=self._call_timeout,  # httpx timeout
                )

                # Use asyncio.wait_for with slightly higher timeout than httpx timeout
                # to allow httpx to raise its own timeout
                response = await asyncio.wait_for(coro, timeout=self._call_timeout + 2)

                content = None
                try:
                    content = response.choices[0].message.content.strip()
                except Exception as e:
                    print(f"Analyzer: Failed to extract response content: {e}")
                    content = str(response)[:200]

                print(f"Analyzer raw response: {content}")

                try:
                    result = json.loads(content)
                except json.JSONDecodeError as e:
                    print(f"Analyzer: JSON parse error: {e}. Response was: {content[:200]}")
                    # Try to extract is_issue status from response text
                    result = {
                        "is_issue": "error" in content.lower() or "critical" in content.lower(),
                        "issue_type": "llm_malformed_response",
                        "explanation": "LLM returned non-JSON response"
                    }
                    return result

                # Validate result structure
                if not isinstance(result, dict):
                    return {
                        "is_issue": False,
                        "issue_type": "invalid_format",
                        "explanation": "LLM response was not a dict"
                    }

                return {
                    "is_issue": result.get("is_issue", False),
                    "issue_type": result.get("issue_type", "unknown"),
                    "explanation": result.get("explanation", "No explanation provided")
                }

            except asyncio.TimeoutError as e:
                last_exc = e
                print(f"Analyzer: Groq request timed out (attempt {attempt}/{self._call_retries + 1}) after {self._call_timeout}s")

            except Exception as e:
                last_exc = e
                print(f"Analyzer: Error on attempt {attempt}/{self._call_retries + 1}: {type(e).__name__}: {e}")

            # Small backoff between attempts
            if attempt <= self._call_retries:
                backoff = 0.5 * attempt
                print(f"Analyzer: Waiting {backoff}s before retry...")
                await asyncio.sleep(backoff)

        # If we reach here, all retry attempts failed
        print(f"Analyzer: All {self._call_retries + 1} attempts failed. Returning safe fallback.")
        
        return {
            "is_issue": True,
            "issue_type": "analysis_unavailable",
            "explanation": "Could not contact LLM service; returned with unavailable status",
            "error": str(last_exc)[:100] if last_exc else "Unknown error"
        }

