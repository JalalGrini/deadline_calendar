import mysql.connector
from dotenv import load_dotenv
import os

load_dotenv()

def init_db():
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS clients (
            id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(255) NOT NULL,
            ice VARCHAR(255),
            if_number VARCHAR(255),
            email VARCHAR(255),
            phone VARCHAR(255),
            type VARCHAR(255)
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS deadlines (
            id INT AUTO_INCREMENT PRIMARY KEY,
            client_id INT,
            type VARCHAR(255),
            period VARCHAR(255),
            due_date DATE,
            status VARCHAR(255),
            FOREIGN KEY(client_id) REFERENCES clients(id)
        )
    """)
    conn.commit()
    conn.close()

def get_connection():
    return mysql.connector.connect(
        host=os.getenv("MYSQL_HOST"),
        port=int(os.getenv("MYSQL_PORT", 3306)),
        user=os.getenv("MYSQL_USER"),
        password=os.getenv("MYSQL_PASSWORD"),
        database=os.getenv("MYSQL_DB")
    )
