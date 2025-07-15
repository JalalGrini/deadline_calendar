import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
from database import get_connection
from dotenv import load_dotenv
import os
import re
import requests

EMAIL_REGEX = re.compile(r"[^@]+@[^@]+\.[^@]+")


def is_valid_email(email):
    return bool(email) and EMAIL_REGEX.match(email)


load_dotenv()

SMTP_SERVER = os.getenv("SMTP_SERVER")
SMTP_PORT = int(os.getenv("SMTP_PORT"))
# Your company/accountant email here
EMAIL_ADDRESS = os.getenv("EMAIL_ADDRESS")
# Your email app password or actual password
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")

print(f"SMTP_SERVER: {SMTP_SERVER}")
print(f"SMTP_PORT: {SMTP_PORT}")
print(f"EMAIL_ADDRESS: {EMAIL_ADDRESS}")
print(
    f"EMAIL_PASSWORD length: {len(EMAIL_PASSWORD) if EMAIL_PASSWORD else 'None'}")


def send_email(to_email, subject, message):
    msg = MIMEMultipart()
    msg["From"] = EMAIL_ADDRESS
    msg["To"] = to_email
    msg["Subject"] = subject
    msg.attach(MIMEText(message, "plain"))

    with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
        server.starttls()
        server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
        server.send_message(msg)
        print("✅ Login successful!")


def send_reminders(days_before=1):
    conn = get_connection()
    if (not conn):
        print("❌ Failed to connect to the database.")
        return
    c = conn.cursor()

    reminder_date = (datetime.now() +
                     timedelta(days=days_before)).strftime("%Y-%m-%d")

    query = """
    SELECT c.name, c.email, d.type, d.period, d.due_date
    FROM deadlines d
    JOIN clients c ON d.client_id = c.id
    WHERE d.status = 'Pending' AND d.due_date = %s
    ORDER BY d.due_date ASC
    """

    c.execute(query, (reminder_date,))

    rows = c.fetchall()
    conn.close()

    if not rows:
        print("No upcoming deadlines to remind.")
        return

    # Group deadlines by client email
    from collections import defaultdict
    client_deadlines = defaultdict(list)
    for name, email, task_type, period, due_date in rows:
        client_deadlines[email].append(
            f"{name} - {task_type} - {period} - Due {due_date}")

    # Send email to each client
    for email, lines in client_deadlines.items():
        print(f"Client email: {email!r}")
        if not is_valid_email(email):
            print(f"Skipping invalid email: {email!r}")
            continue
        message = "Upcoming deadlines:\n\n" + "\n".join(lines)
        subject = f"Reminder: {len(lines)} deadline(s) due tomorrow"
        send_email(email, subject, message)
