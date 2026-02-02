import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import asyncio


class EmailNotifier:
    async def send_email(self, issue_type, explanation, original_log):

        sender_email = os.getenv("SENDER_EMAIL")
        sender_password = os.getenv("SENDER_PASSWORD")
        recipient_email = os.getenv("RECIPIENT_EMAIL")
        smtp_server = os.getenv("SMTP_SERVER")
        smtp_port = int(os.getenv("SMTP_PORT", 587))

        if not all([sender_email, sender_password, recipient_email]):
            print("SMTP config missing — email skipped")
            return

        msg = MIMEMultipart()
        msg["From"] = sender_email
        msg["To"] = recipient_email
        msg["Subject"] = f"[ALERT] {issue_type}"

        body = f"""
Issue detected:

{explanation}

Original log:
{original_log}
"""
        msg.attach(MIMEText(body, "plain"))

        def send():
            with smtplib.SMTP(smtp_server, smtp_port) as server:
                server.starttls()
                server.login(sender_email, sender_password)
                server.send_message(msg)

        await asyncio.to_thread(send)

        print("✅ REAL EMAIL SENT")
