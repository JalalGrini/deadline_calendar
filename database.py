import sqlite3
from dotenv import load_dotenv
import os

load_dotenv()

def init_db():
    conn = sqlite3.connect(os.getenv("DB_PATH"))
    c = conn.cursor()

    c.execute('''
    CREATE TABLE IF NOT EXISTS clients (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        ice TEXT,
        if_number TEXT,
        email TEXT,
        phone TEXT,
        type TEXT
    )
    ''')


    c.execute('''
    CREATE TABLE IF NOT EXISTS deadlines (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        client_id INTEGER,
        type TEXT,
        period TEXT,
        due_date TEXT,
        status TEXT,
        FOREIGN KEY(client_id) REFERENCES clients(id)
    )''')

    conn.commit()
    conn.close()

def get_connection():
    return sqlite3.connect(os.getenv("DB_PATH"))
