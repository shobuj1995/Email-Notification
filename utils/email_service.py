import smtplib
import os
import json
from email.mime.text import MIMEText
from dotenv import load_dotenv

load_dotenv()


def send_email(to_emails, subject, message):

    try:
        sender_email = os.getenv("EMAIL_USER")
        sender_password = os.getenv("EMAIL_PASSWORD")

        # If single email → convert to list
        if isinstance(to_emails, str):
            try:
                to_emails = json.loads(to_emails)
            except:
                to_emails = [to_emails]

        server = smtplib.SMTP_SSL("smtp.gmail.com", 465)
        server.login(sender_email, sender_password)

        for email in to_emails:
            msg = MIMEText(message)
            msg["Subject"] = subject
            msg["From"] = sender_email
            msg["To"] = email

            server.send_message(msg)

        server.quit()

        print("Email sent successfully")

    except Exception as e:
        print("Email sending failed:", e)