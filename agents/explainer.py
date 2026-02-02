from groq import AsyncGroq
import os


class IssueExplainer:
    def __init__(self):
        self.client = AsyncGroq(api_key=os.getenv("GROQ_API_KEY"))

    async def explain_issue(self, log_line, analysis_result):
        """
        Generates a detailed structured explanation for detected issues.
        """
        print(
            f"Agent 3 (Explainer): Generating explanation for {analysis_result['issue_type']}..."
        )

        prompt = f"""
You are a senior Site Reliability Engineer (SRE).

Analyze the following production error log and generate a structured incident explanation.

Log:
"{log_line}"

Analysis Context:
{analysis_result}

Return the response in EXACTLY the following format:

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
- Do NOT add extra commentary.
- Follow the format strictly.
"""

        try:
            chat_completion = await self.client.chat.completions.create(
                messages=[
                    {
                        "role": "system",
                        "content": "You are a highly experienced production SRE.",
                    },
                    {
                        "role": "user",
                        "content": prompt,
                    },
                ],
                model="llama-3.3-70b-versatile",
                temperature=0.4,
            )

            return chat_completion.choices[0].message.content

        except Exception as e:
            print(f"Agent 3 Error: {e}")
            return (
                "Technical Issue:\n"
                "- Unable to analyze the error.\n\n"
                "Possible Cause:\n"
                "- LLM processing failure.\n\n"
                "Suggested Fix:\n"
                "1. Retry the analysis.\n"
                "2. Check LLM service availability."
            )
