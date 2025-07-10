import streamlit as st
from database import init_db, get_connection
import pandas as pd
from datetime import datetime
import sqlite3
import email_utils 
import footer 
from dotenv import load_dotenv
import os

load_dotenv()

init_db()
st.set_page_config("📅 Deadline Calendar")
st.title("📅 Deadline Calendar Manager")

tabs = st.tabs(["Add Client", "Add Deadline", "View Deadlines"])

with tabs[0]:
    st.subheader("➕ Add New Client")

    name = st.text_input("Client Name / Company")
    ice = st.text_input("ICE")
    if_number = st.text_input("IF (Identifiant Fiscal)")
    email = st.text_input("Email")
    phone = st.text_input("Phone Number")
    client_type = st.selectbox("Client Type", ["SARL", "Auto-Entrepreneur", "SAS", "Other"])

    if st.button("Save Client"):
        if not name or not ice:
            st.warning("Client name and ICE are required.")
        else:
            conn = get_connection()
            c = conn.cursor()
            c.execute("""
                INSERT INTO clients (name, ice, if_number, email, phone, type)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (name, ice, if_number, email, phone, client_type))
            conn.commit()
            conn.close()
            st.success(f"Client '{name}' added successfully ✅")

with tabs[1]:
    st.subheader("📌 Add Deadline for a Client")

    # Load clients from DB
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT id, name FROM clients")
    clients = c.fetchall()
    conn.close()

    if not clients:
        st.warning("⚠️ You must add at least one client before adding deadlines.")
    else:
        # Client selection
        client_dict = {f"{name} (ID {client_id})": client_id for client_id, name in clients}
        selected_client = st.selectbox("Select Client", list(client_dict.keys()))
        client_id = client_dict[selected_client]

        # Deadline details
        task_type = st.selectbox("Deadline Type", ["TVA", "CNSS", "IR", "IS", "Other"])
        period = st.text_input("Period (e.g., June 2025 or Q2 2025)")
        due_date = st.date_input("Due Date")
        status = st.selectbox("Status", ["Pending", "Done"])

        if st.button("Add Deadline"):
            conn = get_connection()
            c = conn.cursor()
            c.execute("""
                INSERT INTO deadlines (client_id, type, period, due_date, status)
                VALUES (?, ?, ?, ?, ?)
            """, (client_id, task_type, period, due_date.strftime("%Y-%m-%d"), status))
            conn.commit()
            conn.close()
            st.success("✅ Deadline added successfully!")

with tabs[2]:
    st.subheader("📋 All Client Deadlines")

    # Load all deadlines with client info
    conn = get_connection()
    query = """
    SELECT 
        deadlines.id AS deadline_id,
        clients.name AS client_name,
        clients.type AS client_type,
        deadlines.type AS deadline_type,
        deadlines.period,
        deadlines.due_date,
        deadlines.status
    FROM deadlines
    JOIN clients ON deadlines.client_id = clients.id
    ORDER BY deadlines.due_date ASC
    """

    df = pd.read_sql_query(query, conn)

    conn.close()

    # Check if empty
    if df.empty:
        st.info("No deadlines found.")
    else:
        # Search and filter
        with st.expander("🔍 Filter"):
            search_name = st.text_input("Search by Client Name")
            selected_status = st.selectbox("Filter by Status", ["All", "Pending", "Done"])

            if search_name:
                df = df[df['client_name'].str.contains(search_name, case=False)]

            if selected_status != "All":
                df = df[df['status'] == selected_status]

        st.dataframe(df, use_container_width=True)

        # Delete deadline
        with st.expander("🗑️ Delete a Deadline"):
            deadline_ids = df["deadline_id"].tolist()
            to_delete = st.selectbox("Select deadline ID to delete", deadline_ids)

            if st.button("Delete Deadline"):
                conn = get_connection()
                c = conn.cursor()
                c.execute("DELETE FROM deadlines WHERE id = ?", (to_delete,))
                conn.commit()
                conn.close()
                st.success("Deadline deleted.")
                st.experimental_rerun()

footer.footer()

if __name__ == "__main__":
    recipient = os.getenv("RECIPIENT_EMAIL")
    email_utils.send_reminders(recipient_email=recipient, days_before=1)


