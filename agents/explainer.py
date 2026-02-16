from groq import AsyncGroq
import os
import asyncio


class IssueExplainer:
    def __init__(self):
        _key = os.getenv("GROQ_API_KEY")
        if _key is not None:
            _key = _key.strip()
        self.client = AsyncGroq(api_key=_key)
        
        # Call timeout configuration
        try:
            self._call_timeout = float(os.getenv("GROQ_CALL_TIMEOUT", "30"))
        except Exception:
            self._call_timeout = 30.0

    async def explain_issue(self, log_line, analysis_result):
        """
        Generates a detailed structured explanation for detected issues.
        Returns a string with the explanation or a safe fallback on error.
        """
        print(
            f"Agent 3 (Explainer): Generating explanation for {analysis_result.get('issue_type', 'unknown')}..."
        )

        if not isinstance(analysis_result, dict):
            print("Explainer: Invalid analysis result type")
            return "Unable to generate explanation: invalid analysis format"

        prompt = f"""You are a senior Site Reliability Engineer (SRE).

Analyze the following production error log and generate a structured incident explanation.

Log:
"{log_line}"

Analysis Context:
Issue Type: {analysis_result.get('issue_type', 'unknown')}
Analysis: {analysis_result.get('explanation', 'No analysis provided')}

Return the response in EXACTLY the following format (NO MARKDOWN, plain text only):

Technical Issue:
- Explain clearly what went wrong.

Possible Cause:
- Describe the most likely reason for this issue.

Suggested Fix:
1. Step-by-step actions to resolve the issue.
2. Include system-level or code-level recommendations.
3. Keep it practical and actionable.

Rules:
- Do NOT write paragraphs.
- Do NOT merge sections.
- Do NOT use markdown.
- Follow the format strictly.
"""

        try:
            chat_completion = await asyncio.wait_for(
                self.client.chat.completions.create(
                    messages=[
                        {
                            "role": "system",
                            "content": "You are a highly experienced production SRE. Respond with plain text only.",
                        },
                        {
                            "role": "user",
                            "content": prompt,
                        },
                    ],
                    model="llama-3.3-70b-versatile",
                    temperature=0.4,
                    timeout=self._call_timeout,
                ),
                timeout=self._call_timeout + 2
            )

            explanation = chat_completion.choices[0].message.content
            print("Explainer: Successfully generated explanation")
            return explanation

        except asyncio.TimeoutError as e:
            print(f"Explainer: Request timed out after {self._call_timeout}s")
            return self._get_fallback_explanation(analysis_result)
            
        except Exception as e:
            print(f"Explainer: Error - {type(e).__name__}: {e}")
            return self._get_fallback_explanation(analysis_result)

    @staticmethod
    def _get_fallback_explanation(analysis_result):
        """
        Returns a structured fallback explanation when LLM is unavailable.
        """
        issue_type = analysis_result.get("issue_type", "unknown")
        
        fallback_map = {
            "NullPointerException": """Technical Issue:
- A null pointer reference was attempted in the code.

Possible Cause:
- A method is trying to access properties of a null object.
- Missing input validation before object usage.

Suggested Fix:
1. Add null checks before dereferencing objects.
2. Implement proper input validation.
3. Review the stack trace to identify the exact line.
4. Add defensive programming patterns.""",
            
            "timeout": """Technical Issue:
- Operation exceeded the specified timeout duration.

Possible Cause:
- Slow network or database response.
- Resource contention or system overload.
- Insufficient connection pool size.

Suggested Fix:
1. Increase timeout values appropriately.
2. Profile slow operations.
3. Check resource utilization (CPU, memory, disk).
4. Review database query performance.""",
            
            "memory": """Technical Issue:
- Out of memory error or memory pressure detected.

Possible Cause:
- Memory leak in application code.
- Excessive object allocation.
- Non-release of resources.

Suggested Fix:
1. Enable heap dumps and analyze for leaks.
2. Increase heap size if memory is legitimately needed.
3. Review object lifecycle management.
4. Profile memory usage during operation.""",
        }
        
        # Return specific fallback if available, otherwise generic
        for key, fallback in fallback_map.items():
            if key.lower() in issue_type.lower():
                return fallback
        
        # Generic fallback
        return f"""Technical Issue:
- {analysis_result.get('explanation', 'Unknown issue detected')}.

Possible Cause:
- Check application logs for more details.
- Review recent configuration or deployment changes.

Suggested Fix:
1. Investigate the root cause using logs and metrics.
2. Check system resource availability.
3. Restart the service if appropriate.
4. Escalate if issue persists."""

