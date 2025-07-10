import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
from database import get_connection
from dotenv import load_dotenv
import os

load_dotenv()

SMTP_SERVER = os.getenv("SMTP_SERVER")
SMTP_PORT = int(os.getenv("SMTP_PORT"))
EMAIL_ADDRESS = os.getenv("EMAIL_ADDRESS")       # Your company/accountant email here
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")          # Your email app password or actual password

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

def send_reminders(recipient_email, days_before=1):
    conn = get_connection()
    c = conn.cursor()

    reminder_date = (datetime.now() + timedelta(days=days_before)).strftime("%Y-%m-%d")

    query = """
    SELECT c.name, d.type, d.period, d.due_date
    FROM deadlines d
    JOIN clients c ON d.client_id = c.id
    WHERE d.status = 'Pending' AND d.due_date = ?
    ORDER BY d.due_date ASC
    """

    c.execute(query, (reminder_date,))
    rows = c.fetchall()
    conn.close()

    if not rows:
        print("No upcoming deadlines to remind.")
        return

    lines = [f"{name} - {task_type} - {period} - Due {due_date}" for name, task_type, period, due_date in rows]
    message = "Upcoming deadlines:\n\n" + "\n".join(lines)
    subject = f"Reminder: {len(rows)} deadline(s) due tomorrow"

    send_email(recipient_email, subject, message)
