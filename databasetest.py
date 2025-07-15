import mysql.connector
from mysql.connector import Error
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

def test_db_connection():
    try:
        connection = mysql.connector.connect(
            host=os.getenv("MYSQL_HOST"),
            user=os.getenv("MYSQL_USER"),
            password=os.getenv("MYSQL_PASSWORD"),
            database=os.getenv("MYSQL_DB"),
        )

        if connection.is_connected():
            print("✅ Connection successful!")
            cursor = connection.cursor()

            # Print database version
            cursor.execute("SELECT VERSION();")
            db_version = cursor.fetchone()[0]
            print(f"MySQL Database Version: {db_version}")

            print("\n👥 Fetching sample clients:")
            cursor.execute("SELECT id, name, email, phone FROM clients LIMIT 5;")
            clients = cursor.fetchall()
            for client in clients:
                print(f" - ID: {client[0]}, Name: {client[1]}, Email: {client[2]}, Phone: {client[3]}")

            print("\n📅 Fetching upcoming deadlines:")
            cursor.execute("""
                SELECT c.name, d.type, d.period, d.due_date, d.status
                FROM deadlines d
                JOIN clients c ON d.client_id = c.id
                WHERE d.due_date >= CURDATE()
                ORDER BY d.due_date ASC
                LIMIT 5;
            """)
            deadlines = cursor.fetchall()
            for deadline in deadlines:
                print(f" - Client: {deadline[0]}, Task: {deadline[1]}, Period: {deadline[2]}, Due: {deadline[3]}, Status: {deadline[4]}")

            cursor.close()
            connection.close()
            print("\n✅ Connection closed.")

        else:
            print("❌ Connection failed.")

    except Error as e:
        print("❌ Error while connecting to MySQL:", e)

if __name__ == "__main__":
    test_db_connection()
