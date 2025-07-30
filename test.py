import psycopg2
import os
from dotenv import load_dotenv
from database import get_connection

# Example: set your DATABASE_URL as environment variable, e.g.
# export DATABASE_URL="postgresql://user:password@host:port/dbname"


conn = get_connection()
cur = conn.cursor()

# Drop sms_sent column from users table
drop_column_query = """
ALTER TABLE users
DROP COLUMN IF EXISTS sms_sent;
"""
cur.execute(drop_column_query)
conn.commit()
print("Column sms_sent dropped from users table.")

# Add sms_sent column to deadlines table as boolean default false
add_column_query = """
ALTER TABLE deadlines
ADD COLUMN IF NOT EXISTS sms_sent BOOLEAN DEFAULT FALSE;
"""
cur.execute(add_column_query)
conn.commit()
print("Column sms_sent added to deadlines table.")

cur.close()
conn.close()
