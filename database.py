import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()
DATABASE_URL = os.getenv("CONNECTION_URL")
if DATABASE_URL is None:
    print("🚫 CONNECTION_URL is not set!")
elif "localhost" in DATABASE_URL or "127.0.0.1" in DATABASE_URL:
    print("📦 Loaded CONNECTION_URL (from local .env):", DATABASE_URL)
else:
    print("🔐 Loaded CONNECTION_URL (likely from GitHub Secrets):", DATABASE_URL)

def get_connection():
    return psycopg2.connect(DATABASE_URL)

def init_db():
    conn = get_connection()
    c = conn.cursor()

    # Create users table
    c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            username VARCHAR(255) NOT NULL UNIQUE,
            password_hash VARCHAR(255) NOT NULL,
            name VARCHAR(255) NOT NULL,
            email VARCHAR(255) NOT NULL UNIQUE,
            phone VARCHAR(20),
            registered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            approved BOOLEAN DEFAULT FALSE,
            approved_by VARCHAR(255),
            approved_at TIMESTAMP
        )
    """)

    # Create clients table with user_id foreign key
    c.execute("""
        CREATE TABLE IF NOT EXISTS clients (
            id SERIAL PRIMARY KEY,
            user_id INT,
            name VARCHAR(255) NOT NULL,
            ice VARCHAR(255),
            if_number VARCHAR(255),
            email VARCHAR(255),
            phone VARCHAR(255),
            type VARCHAR(255),
            FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE SET NULL
        )
    """)

    # Create deadlines table with client_id foreign key
    c.execute("""
        CREATE TABLE IF NOT EXISTS deadlines (
            id SERIAL PRIMARY KEY,
            client_id INT,
            type VARCHAR(255),
            period VARCHAR(255),
            due_date DATE,
            status VARCHAR(255),
            email_sent BOOLEAN DEFAULT FALSE,
            sms_sent BOOLEAN DEFAULT FALSE,
            FOREIGN KEY(client_id) REFERENCES clients(id) ON DELETE CASCADE
        )
    """)

    # Create notes table
    c.execute("""
        CREATE TABLE IF NOT EXISTS notes (
            id SERIAL PRIMARY KEY,
            user_id INT NOT NULL,
            content TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        )
    """)

    # Create email_logs table
    c.execute("""
        CREATE TABLE IF NOT EXISTS email_logs (
            id SERIAL PRIMARY KEY,
            user_id INT,
            deadline_id INT,
            sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE,
            FOREIGN KEY(deadline_id) REFERENCES deadlines(id) ON DELETE CASCADE
        )
    """)

    # Create sms_logs table
    c.execute("""
        CREATE TABLE IF NOT EXISTS sms_logs (
            id SERIAL PRIMARY KEY,
            user_id INT,
            deadline_id INT,
            phone VARCHAR(20),
            message TEXT,
            sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE,
            FOREIGN KEY(deadline_id) REFERENCES deadlines(id) ON DELETE CASCADE
        )
    """)

    # Create message_templates table
    c.execute("""
        CREATE TABLE IF NOT EXISTS message_templates (
            id SERIAL PRIMARY KEY,
            user_id INT NOT NULL,
            email_message TEXT,
            sms_message TEXT,
            email_subject VARCHAR(255),
            deadline_type VARCHAR(255),
            client_id INT,
            days_before INT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE,
            FOREIGN KEY(client_id) REFERENCES clients(id) ON DELETE SET NULL
        )
    """)

    conn.commit()
    c.close()
    conn.close()

def get_all_users():
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM users")
    rows = c.fetchall()
    conn.close()
    return [dict(zip([col[0] for col in c.description], row)) for row in rows]

def get_clients_by_user_id(user_id):
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM clients WHERE user_id = %s", (user_id,))
    rows = c.fetchall()
    conn.close()
    return [dict(zip([col[0] for col in c.description], row)) for row in rows]

def get_deadlines_by_client_id(client_id):
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM deadlines WHERE client_id = %s", (client_id,))
    rows = c.fetchall()
    conn.close()
    return [dict(zip([col[0] for col in c.description], row)) for row in rows]

def delete_user(user_id):
    conn = get_connection()
    c = conn.cursor()
    c.execute("DELETE FROM users WHERE id = %s", (user_id,))
    conn.commit()
    conn.close()

def delete_client(client_id):
    conn = get_connection()
    c = conn.cursor()
    c.execute("DELETE FROM clients WHERE id = %s", (client_id,))
    conn.commit()
    conn.close()

def delete_deadline(deadline_id):
    conn = get_connection()
    c = conn.cursor()
    c.execute("DELETE FROM deadlines WHERE id = %s", (deadline_id,))
    conn.commit()
    conn.close()