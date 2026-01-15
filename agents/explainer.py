from groq import AsyncGroq
import os

class IssueExplainer:
    def __init__(self):
        self.client = AsyncGroq(api_key=os.getenv("GROQ_API_KEY"))

    async def explain_issue(self, log_line, analysis_result):
        """
        Generates a detailed explanation and recommended fix for an issue.
        """
        print(f"Agent 3 (Explainer): Generating explanation for {analysis_result['issue_type']}...")

        prompt = f"""
        Explain this technical issue in simple terms and suggest a fix.
        
        Log: "{log_line}"
        Context: {analysis_result}
        
        Be concise (max 3 sentences).
        """

        try:
            chat_completion = await self.client.chat.completions.create(
                messages=[
                    {
                        "role": "system",
                        "content": "You are a helpful SRE assistant.",
                    },
                    {
                        "role": "user",
                        "content": prompt,
                    }
                ],
                model="llama3-70b-8192", # Using a bigger model for better explanation
                temperature=0.5,
            )
            
            return chat_completion.choices[0].message.content

        except Exception as e:
            print(f"Agent 3 Error: {e}")
            return "Could not generate explanation."
