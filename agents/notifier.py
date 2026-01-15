import asyncio

class EmailNotifier:
    async def send_email(self, issue_type, explanation, original_log):
        """
        Simulates sending an email alert.
        """
        print(f"\nExample Email ------------------------------------------------")
        print(f"To: admin@company.com")
        print(f"Subject: [ALERT] {issue_type} Detected")
        print(f"--------------------------------------------------------------")
        print(f"Body:")
        print(f"{explanation}")
        print(f"\nOriginal Log: {original_log}")
        print(f"--------------------------------------------------------------\n")
        
        # Simulate network latency for sending email
        await asyncio.sleep(0.5)
        print("Agent 4 (Notifier): Email sent successfully.")
