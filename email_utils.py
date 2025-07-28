import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
from database import get_connection
from auth import get_user_id
from dotenv import load_dotenv
import os
import re
from dateutil.relativedelta import relativedelta
from collections import defaultdict

EMAIL_REGEX = re.compile(r"[^@]+@[^@]+\.[^@]+")

# Function to validate email format
def is_valid_email(email):
    return bool(email) and EMAIL_REGEX.match(email)

# Load environment variables
load_dotenv()

SMTP_SERVER = os.getenv("SMTP_SERVER")
SMTP_PORT = int(os.getenv("SMTP_PORT"))

EMAIL_ADDRESS = os.getenv("EMAIL_ADDRESS")

EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")

def get_user_id_by_email(email):
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
        SELECT user_id FROM clients WHERE email = %s LIMIT 1
    """, (email,))
    result = c.fetchone()
    conn.close()
    if result:
        return result[0]
    else:
        return None
    


def log_email_sent(user_id, deadline_id):
    conn = get_connection()
    c = conn.cursor()
    c.execute("INSERT INTO email_logs (user_id, deadline_id) VALUES (%s, %s)", (user_id, deadline_id))
    conn.commit()
    conn.close()

# Function to send email
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

def send_reminders(days_list=[1], username=None):
    user_id = get_user_id(username) if username else None
    
    conn = get_connection()
    c = conn.cursor()
    c.execute("UPDATE deadlines SET email_sent = FALSE WHERE email_sent = TRUE")
    conn.commit()
    conn.close()

    for days_before in days_list:
        conn = get_connection()
        if not conn:
            print("❌ Failed to connect to the database.")
            return
        c = conn.cursor()

        reminder_date = (datetime.now() +
                        timedelta(days=days_before)).strftime("%Y-%m-%d")

        query = """
        SELECT c.name, c.email, d.type, d.period, d.due_date, d.id AS deadline_id
        FROM deadlines d
        JOIN clients c ON d.client_id = c.id
        WHERE d.status = 'Pending' AND d.due_date = %s
        """
        params = (reminder_date,)
        
        if user_id:
            query += " AND c.user_id = %s"
            params += (user_id,)

        query += " ORDER BY d.due_date ASC"
        
        c.execute(query, params)
        rows = c.fetchall()
        conn.close()

        if not rows:
            print(
                f"No upcoming deadlines to remind for {days_before} days before.")
            continue

        client_deadlines = defaultdict(list)
        for row in rows:
            name, email, task_type, period, due_date, deadline_id = row
            client_deadlines[email].append({
                "text": f"{name} - {task_type} - {period} - Due {due_date} ({days_before} days left)",
                "deadline_id": deadline_id
            })

        for email, lines in client_deadlines.items():
            lines_str = "\n".join([line["text"] for line in lines])
            print(f"Client email: {email!r}")
            if not is_valid_email(email):
                print(f"Skipping invalid email: {email!r}")
                continue
            message = (
                f"Bonjour,\n\n"
                f"Il reste {days_before} jour(s) avant l'échéance suivante :\n\n"
                f"{lines_str}\n\n"
                "\n\nMerci de prendre les mesures nécessaires."
            )
            subject = f"Rappel : {len(lines)} échéance(s) dans {days_before} jour(s)"
            try:
                send_email(email, subject, message)
                for line in lines:
                    log_email_sent(user_id, line["deadline_id"])

                # Mark as sent in DB for each deadline
                conn = get_connection()
                c = conn.cursor()
                for line in lines:
                    c.execute("""
                        UPDATE deadlines 
                        SET email_sent = TRUE 
                        WHERE id = %s
                    """, (line["deadline_id"],))
                conn.commit()
                conn.close()

                print(f"✅ Email sent and marked as sent for {email}")
            except Exception as e:
                print(f"❌ Failed to send email to {email}: {e}")

def send_individual_email(deadline_id):
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
        SELECT c.name, c.email, d.type, d.period, d.due_date
        FROM deadlines d
        JOIN clients c ON d.client_id = c.id
        WHERE d.id = %s
        LIMIT 1
    """, (deadline_id,))
    row = c.fetchone()
    if not row:
        conn.close()
        raise ValueError("Deadline not found.")
    name, email, task_type, period, due_date = row
    if not is_valid_email(email):
        conn.close()
        raise ValueError(f"Invalid email: {email}")
    user_id = get_user_id_by_email(email)
    if user_id is None:
        conn.close()
        raise ValueError("User ID not found for this email.")


    

    subject = f"Reminder: {task_type} deadline"
    message = (
        f"Bonjour {name},\n\n"
        f"Ceci est un rappel pour la tâche suivante :\n"
        f"- Type: {task_type}\n"
        f"- Période: {period}\n"
        f"- Date limite: {due_date}\n\n"
        "Merci de prendre les mesures nécessaires."
    )

    send_email(email, subject, message)
    log_email_sent(user_id, deadline_id)
    c.execute("UPDATE deadlines SET email_sent = TRUE WHERE id = %s",
              (deadline_id,))
    conn.commit()
    conn.close()

def process_today_deadlines():
    conn = get_connection()
    c = conn.cursor()
    today = datetime.now().date()
    today_str = today.strftime("%Y-%m-%d")
    c.execute("""
        SELECT id, period, due_date
        FROM deadlines
        WHERE due_date = %s
    """, (today_str,))
    deadlines = c.fetchall()

    for deadline_id, period, due_date in deadlines:
        if isinstance(due_date, str):
            due_date = datetime.strptime(due_date, "%Y-%m-%d").date()

        if period.lower() == "mensuel":
            new_due = due_date + relativedelta(months=1)
            c.execute("UPDATE deadlines SET due_date = %s WHERE id = %s",
                      (new_due.strftime("%Y-%m-%d"), deadline_id))
        elif period.lower() == "trimestriel":
            new_due = due_date + relativedelta(months=3)
            c.execute("UPDATE deadlines SET due_date = %s WHERE id = %s",
                      (new_due.strftime("%Y-%m-%d"), deadline_id))
        elif period.lower() == "annuel":
            new_due = due_date + relativedelta(years=1)
            c.execute("UPDATE deadlines SET due_date = %s WHERE id = %s",
                      (new_due.strftime("%Y-%m-%d"), deadline_id))
        elif period.lower() == "one time":
            c.execute("DELETE FROM deadlines WHERE id = %s", (deadline_id,))
    conn.commit()
    conn.close()

if __name__ == "__main__":
    send_reminders(days_list=[20, 10, 5, 1])
    process_today_deadlines()