import streamlit as st
import streamlit_authenticator as stauth
import yaml
from yaml.loader import SafeLoader
from database import get_connection
import mysql.connector

def init_auth():
    try:
        with open('users.yaml', 'r') as file:
            config = yaml.load(file, Loader=SafeLoader)
    except FileNotFoundError:
        config = {
            'credentials': {
                'usernames': {}
            },
            'cookie': {
                'expiry_days': 30,
                'key': 'random_signature_key',
                'name': 'deadline_calendar'
            }
        }
    
    authenticator = stauth.Authenticate(
        credentials=config['credentials'],
        cookie_name=config['cookie']['name'],
        cookie_key=config['cookie']['key'],
        cookie_expiry_days=config['cookie']['expiry_days']
    )
    return authenticator, config

def save_user_to_db(username, name, email, password):
    conn = get_connection()
    c = conn.cursor()
    try:
        c.execute("""
            INSERT INTO users (username, password_hash, name, email)
            VALUES (%s, %s, %s, %s)
        """, (username, password, name, email))  # Store plain text password
        conn.commit()
    except mysql.connector.Error as e:
        conn.rollback()
        raise Exception(f"Error creating user: {e}")
    finally:
        conn.close()


#  Function to handle custom login logic
def custom_login(username, password):
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT username, name FROM users WHERE username = %s AND password_hash = %s", (username, password))
    result = c.fetchone()
    conn.close()
    if result:
        return result[0], result[1]  # Return username, name
    return None, None



def get_user_id(username):
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT id FROM users WHERE username = %s", (username,))
    result = c.fetchone()
    conn.close()
    return result[0] if result else None