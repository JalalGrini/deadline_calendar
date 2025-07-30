import os
from datetime import datetime, timedelta
from collections import defaultdict
from database import get_connection
from auth import get_user_id
from dateutil.relativedelta import relativedelta
from dotenv import load_dotenv
from twilio.rest import Client

# Load .env variables
load_dotenv()

# Twilio credentials
TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_PHONE_NUMBER = os.getenv("TWILIO_PHONE_NUMBER")

client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)

def send_sms(to_phone, message):
    try:
        sms = client.messages.create(
            body=message,
            from_=TWILIO_PHONE_NUMBER,
            to=to_phone
        )
        print(f"✅ SMS sent to {to_phone}: {sms.sid}")
    except Exception as e:
        print(f"❌ Failed to send SMS to {to_phone}: {e}")

def send_reminders(days_list=[1], username=None):
    user_id = get_user_id(username) if username else None

    # Reset SMS status
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

        reminder_date = (datetime.now() + timedelta(days=days_before)).strftime("%Y-%m-%d")

        query = """
        SELECT c.name, c.phone, d.type, d.period, d.due_date
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
            print(f"ℹ️ No deadlines for {days_before} days before.")
            continue

        client_deadlines = defaultdict(list)
        for name, phone, task_type, period, due_date in rows:
            client_deadlines[phone].append(
                f"{task_type} ({period}) - échéance le {due_date}"
            )

        for phone, tasks in client_deadlines.items():
            if phone.startswith("0"):
                phone = "+212" + phone[1:]
            if not phone or not phone.startswith("+"):
                print(f"⚠️ Skipping invalid phone: {phone}")
                continue

            message = (
                f"📅 Bonjour,\n"
                f"Il reste {days_before} jour(s) avant:\n" +
                "\n".join(tasks) +
                "\n\nMerci de prendre les mesures nécessaires."
            )

            send_sms(phone, message)

            # Mark as sent
            conn = get_connection()
            c = conn.cursor()
            c.execute("""
                UPDATE deadlines 
                SET email_sent = TRUE 
                WHERE status = 'Pending' AND due_date = %s AND client_id = (
                    SELECT id FROM clients WHERE phone = %s LIMIT 1
                )
            """, (reminder_date, phone))
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
        elif period.lower() == "trimestriel":
            new_due = due_date + relativedelta(months=3)
        elif period.lower() == "annuel":
            new_due = due_date + relativedelta(years=1)
        else:  # One time
            c.execute("DELETE FROM deadlines WHERE id = %s", (deadline_id,))
            continue

        c.execute("UPDATE deadlines SET due_date = %s WHERE id = %s",
                  (new_due.strftime("%Y-%m-%d"), deadline_id))

    conn.commit()
    conn.close()

if __name__ == "__main__":
    send_reminders(days_list=[20, 10, 5, 1])
    process_today_deadlines()
