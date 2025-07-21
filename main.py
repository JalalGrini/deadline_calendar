import streamlit as st
from database import init_db, get_connection
import pandas as pd
from datetime import datetime
import email_utils
import footer
from auth import init_auth, save_user_to_db, get_user_id , custom_login
from dotenv import load_dotenv
import os
import yaml

load_dotenv()

init_db()
st.set_page_config("📅 Deadline Calendar")
st.title("📅 Deadline Calendar Manager")

# Initialize authenticator
authenticator, config = init_auth()

# Authentication
if 'authentication_status' not in st.session_state:
    st.session_state['authentication_status'] = None

if st.session_state['authentication_status'] is None:
    tab1, tab2 = st.tabs(["Login", "Register"])
    
    with tab1:
        st.subheader("Login")
        with st.form("login_form"):
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            submit = st.form_submit_button("Login")
            
            if submit:
                username, name = custom_login(username, password)
                if username:
                    st.session_state['authentication_status'] = True
                    st.session_state['name'] = name
                    st.session_state['username'] = username
                    st.success(f"Welcome {name}")
                    st.rerun()
                else:
                    st.error("Username or password is incorrect")
    
    with tab2:
        st.subheader("Register")
        with st.form("register_form"):
            username = st.text_input("Username")
            name = st.text_input("Full Name")
            email = st.text_input("Email")
            password = st.text_input("Password", type="password")
            submit = st.form_submit_button("Register")
            
            if submit:
                try:
                    # Register user with streamlit-authenticator (modern API)
                    if not username or not name or not email or not password:
                        raise ValueError("All fields are required")
                    # Save to database
                    save_user_to_db(username, name, email, password)
                    # Update config file
                    config['credentials']['usernames'][username] = {
                        'email': email,
                        'name': name,
                        'password': password  # Plain text password
                    }
                    with open('users.yaml', 'w') as file:
                        yaml.dump(config, file)
                    # Auto-login after registration
                    st.session_state['authentication_status'] = True
                    st.session_state['name'] = name
                    st.session_state['username'] = username
                    st.success("Registration successful! You are now logged in.")
                    st.rerun()
                except Exception as e:
                    st.error(f"Registration failed: {e}")

else:
    # Only show logout button if user is logged in
    if st.session_state['authentication_status']:
        authenticator.logout('Logout', 'sidebar')
    
    # Get current user ID
    user_id = get_user_id(st.session_state['username'])
    
    # Sidebar with reminder button
    with st.sidebar:
        if st.button("Send Reminder Emails"):
            try:
                from dotenv import load_dotenv
                load_dotenv(override=True)
                email_utils.send_reminders(days_list=[20, 10, 5, 1], username=st.session_state['username'])
                email_utils.process_today_deadlines()
                st.success("✅ Reminder emails sent successfully!")
            except Exception as e:
                st.error(f"❌ Failed to send reminders: {e}")

    tabs = st.tabs(["Add Client", "Add Deadline", "View Deadlines"])

    with tabs[0]:
        st.subheader("➕ Add New Client")
        name = st.text_input("Client Name / Company")
        ice = st.text_input("ICE")
        if_number = st.text_input("IF (Identifiant Fiscal)")
        email = st.text_input("Email")
        phone = st.text_input("Phone Number")
        client_type = st.selectbox(
            "Client Type", ["SARL", "Auto-Entrepreneur", "SAS", "Other"])

        if st.button("Save Client"):
            if not name or not ice:
                st.warning("Client name and ICE are required.")
            else:
                conn = get_connection()
                c = conn.cursor()
                c.execute("""
                    INSERT INTO clients (user_id, name, ice, if_number, email, phone, type)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                """, (user_id, name, ice, if_number, email, phone, client_type))
                conn.commit()
                conn.close()
                st.success(f"Client '{name}' added successfully ✅")

    with tabs[1]:
        st.subheader("📌 Add Deadline for a Client")
        conn = get_connection()
        c = conn.cursor()
        c.execute("SELECT id, name FROM clients WHERE user_id = %s", (user_id,))
        clients = c.fetchall()
        conn.close()

        if not clients:
            st.warning("⚠️ You must add at least one client before adding deadlines.")
        else:
            client_dict = {
                f"{name} (ID {client_id})": client_id for client_id, name in clients}
            selected_client = st.selectbox(
                "Select Client", list(client_dict.keys()))
            client_id = client_dict[selected_client]

            task_type = st.selectbox(
                "Deadline Type", ["TVA", "CNSS", "IR", "IS", "Other"])
            period = st.selectbox("Période", ["One Time", "Mensuel", "Trimestriel", "Annuel"])
            due_date = st.date_input("Due Date")
            status = st.selectbox("Status", ["Pending", "Done"])

            if st.button("Add Deadline"):
                conn = get_connection()
                c = conn.cursor()
                c.execute("""
                    INSERT INTO deadlines (client_id, type, period, due_date, status)
                    VALUES (%s, %s, %s, %s, %s)
                """, (client_id, task_type, period, due_date.strftime("%Y-%m-%d"), status))
                conn.commit()
                conn.close()
                st.success("✅ Deadline added successfully!")

    with tabs[2]:
        st.subheader("📋 All Client Deadlines")
        conn = get_connection()
        query = """
        SELECT 
            deadlines.id AS deadline_id,
            clients.name AS client_name,
            clients.type AS client_type,
            deadlines.type AS deadline_type,
            deadlines.period,
            deadlines.due_date,
            deadlines.status,
            deadlines.email_sent
        FROM deadlines
        JOIN clients ON deadlines.client_id = clients.id
        WHERE clients.user_id = %s
        ORDER BY deadlines.due_date ASC
        """
        df = pd.read_sql_query(query, conn, params=(user_id,))
        conn.close()

        if df.empty:
            st.info("No deadlines found.")
        else:
            with st.expander("🔍 Filter"):
                search_name = st.text_input("Search by Client Name")
                selected_status = st.selectbox(
                    "Filter by Status", ["All", "Pending", "Done"])

                if search_name:
                    df = df[df['client_name'].str.contains(
                        search_name, case=False)]

                if selected_status != "All":
                    df = df[df['status'] == selected_status]
                
                df["Statut Email"] = df["email_sent"].apply(
                    lambda x: "Envoyé ✅" if x else "Non envoyé ❌")
                df.drop(columns=["email_sent"], inplace=True)
            
            st.dataframe(df, use_container_width=True, hide_index=True)

            with st.expander("🗑️ Delete a Deadline"):
                deadline_ids = df["deadline_id"].tolist()
                to_delete = st.selectbox(
                    "Select deadline ID to delete", deadline_ids)

                if st.button("Delete Deadline"):
                    conn = get_connection()
                    c = conn.cursor()
                    c.execute("DELETE FROM deadlines WHERE id = %s", (to_delete,))
                    conn.commit()
                    conn.close()
                    st.success("Deadline deleted.")
                    st.rerun()

            with st.expander("✉️ Send Individual Email"):
                deadline_ids = df["deadline_id"].tolist()
                to_email_id = st.selectbox(
                    "Select deadline ID to send email", deadline_ids, key="send_email_id"
                )

                if st.button("Send Individual Email"):
                    try:
                        email_utils.send_individual_email(to_email_id)
                        st.success(f"Email sent for deadline ID {to_email_id}.")
                    except Exception as e:
                        st.error(f"Failed to send email: {e}")

footer.footer()
