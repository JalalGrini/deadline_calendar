import mysql.connector
from dotenv import load_dotenv
import os

load_dotenv()

def init_db():
    conn = get_connection()
    c = conn.cursor()
    
    # Create users table
    c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INT AUTO_INCREMENT PRIMARY KEY,
            username VARCHAR(255) NOT NULL UNIQUE,
            password_hash VARCHAR(255) NOT NULL,
            name VARCHAR(255) NOT NULL,
            email VARCHAR(255) NOT NULL UNIQUE
        )
    """)
    
    # Modified clients table with user_id foreign key
    c.execute("""
        CREATE TABLE IF NOT EXISTS clients (
            id INT AUTO_INCREMENT PRIMARY KEY,
            user_id INT,
            name VARCHAR(255) NOT NULL,
            ice VARCHAR(255),
            if_number VARCHAR(255),
            email VARCHAR(255),
            phone VARCHAR(255),
            type VARCHAR(255),
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
    """)
    
    # Modified deadlines table with user_id through client_id
    c.execute("""
    CREATE TABLE IF NOT EXISTS deadlines (
        id INT AUTO_INCREMENT PRIMARY KEY,
        client_id INT,
        type VARCHAR(255),
        period VARCHAR(255),
        due_date DATE,
        status VARCHAR(255),
        email_sent BOOLEAN DEFAULT FALSE,
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
