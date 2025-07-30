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

def is_valid_email(email):
    return bool(email) and EMAIL_REGEX.match(email)

load_dotenv()
SMTP_SERVER = os.getenv("SMTP_SERVER")
SMTP_PORT = int(os.getenv("SMTP_PORT"))
EMAIL_ADDRESS = os.getenv("EMAIL_ADDRESS")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")

def get_user_id_by_email(email):
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT user_id FROM clients WHERE email = %s LIMIT 1", (email,))
    result = c.fetchone()
    conn.close()
    return result[0] if result else None

def log_email_sent(user_id, deadline_id):
    conn = get_connection()
    c = conn.cursor()
    c.execute("INSERT INTO email_logs (user_id, deadline_id) VALUES (%s, %s)", (user_id, deadline_id))
    conn.commit()
    conn.close()

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
        print("✅ Email envoyé avec succès !")

def send_template_emails(user_id):
    print(f"📧 Traitement des emails de modèle pour user_id: {user_id}")
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
        SELECT id, email_message, email_subject, deadline_type, client_id, days_before
        FROM message_templates
        WHERE user_id = %s AND email_message IS NOT NULL
    """, (user_id,))
    templates = c.fetchall()
    conn.close()
    print(f"📋 {len(templates)} modèles trouvés pour user_id {user_id}")

    for template_id, email_message_template, email_subject, deadline_type, client_id, days_before in templates:
        print(f"🔍 Modèle ID {template_id}: days_before={days_before}, deadline_type={deadline_type or 'All'}, client_id={client_id or 'All'}")
        reminder_date = (datetime.now() + timedelta(days=days_before)).date()
        reminder_date_str = reminder_date.strftime("%Y-%m-%d")
        print(f"📅 Date de rappel: {reminder_date_str} (aujourd'hui + {days_before} jours)")

        query = """
            SELECT c.id AS client_id, c.name, c.email, c.type, c.ice, c.if_number,
                   d.type AS deadline_type, d.period, d.due_date, d.status, d.id AS deadline_id
            FROM deadlines d
            JOIN clients c ON d.client_id = c.id
            WHERE d.status = 'Pending' AND DATE(d.due_date) = %s AND d.email_sent = FALSE AND c.user_id = %s
        """
        params = [reminder_date_str, user_id]
        if deadline_type:
            query += " AND d.type = %s"
            params.append(deadline_type)
        if client_id:
            query += " AND c.id = %s"
            params.append(client_id)

        conn = get_connection()
        c = conn.cursor()
        c.execute(query, params)
        rows = c.fetchall()
        conn.close()
        print(f"🔎 {len(rows)} échéances correspondantes trouvées pour le modèle ID {template_id}")

        if not rows:
            print(f"ℹ️ Aucune échéance correspondante pour le modèle ID {template_id} le {reminder_date_str}")
            continue

        for row in rows:
            client_id, client_name, client_email, client_type, ice, if_number, deadline_type, period, due_date, status, deadline_id = row
            if not is_valid_email(client_email):
                print(f"⚠️ Ignorer l'email invalide: {client_email}")
                continue

            try:
                message = email_message_template.format(
                    client_name=client_name,
                    client_email=client_email,
                    client_phone="N/A",
                    client_type=client_type or "N/A",
                    ice=ice or "N/A",
                    if_number=if_number or "N/A",
                    deadline_type=deadline_type,
                    period=period,
                    due_date=due_date,
                    status=status
                )
            except KeyError as e:
                print(f"❌ Variable invalide dans le modèle ID {template_id}: {e}")
                continue

            try:
                send_email(client_email, email_subject or f"Rappel: {deadline_type} ({days_before} jours)", message)
                log_email_sent(user_id, deadline_id)
                conn = get_connection()
                c = conn.cursor()
                c.execute("UPDATE deadlines SET email_sent = TRUE WHERE id = %s", (deadline_id,))
                conn.commit()
                conn.close()
                print(f"✅ Email envoyé à {client_email} pour le modèle ID {template_id}, échéance ID {deadline_id}")
            except Exception as e:
                print(f"❌ Échec de l'envoi de l'email à {client_email}: {e}")

def send_reminders(days_list=[1], username=None):
    user_id = get_user_id(username) if username else None
    
    conn = get_connection()
    c = conn.cursor()
    c.execute("UPDATE deadlines SET email_sent = FALSE WHERE email_sent = TRUE")
    conn.commit()
    conn.close()

    for days_before in days_list:
        conn = get_connection()
        c = conn.cursor()
        reminder_date = (datetime.now() + timedelta(days=days_before)).strftime("%Y-%m-%d")
        query = """
        SELECT c.id AS client_id, c.name, c.email, d.type, d.period, d.due_date, d.id AS deadline_id
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
            print(f"ℹ️ Aucun rappel par défaut pour {days_before} jours avant.")
            continue

        client_deadlines = defaultdict(list)
        for client_id, name, email, task_type, period, due_date, deadline_id in rows:
            client_deadlines[email].append({
                "client_id": client_id,
                "name": name,
                "task_type": task_type,
                "period": period,
                "due_date": due_date,
                "deadline_id": deadline_id
            })

        for email, deadlines in client_deadlines.items():
            if not is_valid_email(email):
                print(f"⚠️ Ignorer l'email invalide: {email}")
                continue

            tasks = "\n".join([f"- {d['task_type']} ({d['period']}) - Due {d['due_date']}" for d in deadlines])
            message = (
                f"Bonjour {deadlines[0]['name']},\n\n"
                f"Il reste {days_before} jour(s) avant l'échéance suivante :\n\n"
                f"{tasks}\n\n"
                f"Merci de prendre les mesures nécessaires."
            )
            subject = f"Rappel : {len(deadlines)} échéance(s) dans {days_before} jour(s)"

            try:
                send_email(email, subject, message)
                conn = get_connection()
                c = conn.cursor()
                for d in deadlines:
                    log_email_sent(user_id or get_user_id_by_email(email), d["deadline_id"])
                    c.execute("UPDATE deadlines SET email_sent = TRUE WHERE id = %s", (d["deadline_id"],))
                conn.commit()
                conn.close()
                print(f"✅ Rappel par défaut envoyé à {email}")
            except Exception as e:
                print(f"❌ Échec de l'envoi du rappel par défaut à {email}: {e}")

    if user_id:
        try:
            send_template_emails(user_id)
            print(f"📧 Emails de modèle traités pour user_id {user_id}")
        except Exception as e:
            print(f"❌ ERREUR lors de l'envoi des emails de modèle pour user_id {user_id}: {e}")

def send_individual_email(deadline_id):
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
        SELECT c.name, c.email, c.id AS client_id, c.type, c.ice, c.if_number,
               d.type AS deadline_type, d.period, d.due_date, u.id AS user_id
        FROM deadlines d
        JOIN clients c ON d.client_id = c.id
        JOIN users u ON c.user_id = u.id
        WHERE d.id = %s
        LIMIT 1
    """, (deadline_id,))
    row = c.fetchone()
    conn.close()

    if not row:
        raise ValueError("Échéance non trouvée.")
    name, email, client_id, client_type, ice, if_number, deadline_type, period, due_date, user_id = row
    if not is_valid_email(email):
        raise ValueError(f"Email invalide: {email}")

    conn = get_connection()
    c = conn.cursor()
    c.execute("""
        SELECT email_message, email_subject
        FROM message_templates
        WHERE user_id = %s
        AND (deadline_type = %s OR deadline_type IS NULL)
        AND (client_id = %s OR client_id IS NULL)
        ORDER BY created_at DESC LIMIT 1
    """, (user_id, deadline_type, client_id))
    template = c.fetchone()
    conn.close()

    if template:
        email_message_template, subject = template
    else:
        email_message_template = (
            f"Bonjour {name},\n\n"
            f"Ceci est un rappel pour la tâche suivante :\n"
            f"- Type: {deadline_type}\n"
            f"- Période: {period}\n"
            f"- Date limite: {due_date}\n\n"
            f"Merci de prendre les mesures nécessaires."
        )
        subject = f"Rappel: échéance {deadline_type}"

    try:
        message = email_message_template.format(
            client_name=name,
            client_email=email,
            client_phone="N/A",
            client_type=client_type or "N/A",
            ice=ice or "N/A",
            if_number=if_number or "N/A",
            deadline_type=deadline_type,
            period=period,
            due_date=due_date,
            status="Pending"
        )
    except KeyError as e:
        raise ValueError(f"Variable invalide dans le modèle: {e}")

    send_email(email, subject, message)
    log_email_sent(user_id, deadline_id)
    conn = get_connection()
    c = conn.cursor()
    c.execute("UPDATE deadlines SET email_sent = TRUE WHERE id = %s", (deadline_id,))
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
        else:  # one time
            c.execute("DELETE FROM deadlines WHERE id = %s", (deadline_id,))
            continue

        c.execute("UPDATE deadlines SET due_date = %s WHERE id = %s",
                  (new_due.strftime("%Y-%m-%d"), deadline_id))

    conn.commit()
    conn.close()

if __name__ == "__main__":
    print("🚀 Démarrage du job de rappel par email pour tous les utilisateurs approuvés")
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT id, username FROM users WHERE approved = TRUE")
    users = c.fetchall()
    conn.close()
    print(f"👥 {len(users)} utilisateurs approuvés trouvés")

    for user_id, username in users:
        print(f"👤 Traitement de l'utilisateur: {username} (ID: {user_id})")
        send_reminders(days_list=[20, 10, 5, 1], username=username)
    process_today_deadlines()
    print("🏁 Job de rappel par email terminé")