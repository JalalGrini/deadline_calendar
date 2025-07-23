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
            email VARCHAR(255) NOT NULL UNIQUE
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
            FOREIGN KEY(client_id) REFERENCES clients(id) ON DELETE CASCADE
        )
    """)

    conn.commit()
    c.close()
    conn.close()

def get_connection():
    return psycopg2.connect(DATABASE_URL)
