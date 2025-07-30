import streamlit as st
from database import get_connection
import pandas as pd
import email_utils

def show_client_deadline_manager(user_id):
    tab = st.radio("Management:", ["Add Client", "Add Deadline", "View Deadlines"])

    if tab == "Add Client":
        st.subheader("➕ Add New Client")
        name = st.text_input("Client Name / Company")
        ice = st.text_input("I.C. E (Identifiant Commun de l'Entreprise)")
        if_number = st.text_input("I.F (Identifiant Fiscal)")
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
                    INSERT INTO clients (user_id, name, ice, if_number, email, phone, type)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                """, (user_id, name, ice, if_number, email, phone, client_type))
                conn.commit()
                conn.close()
                st.success(f"Client '{name}' ajouté avec succès ✅")

    elif tab == "Add Deadline":
        st.subheader("📌 Add Deadline for a Client")
        conn = get_connection()
        c = conn.cursor()
        c.execute("SELECT id, name FROM clients WHERE user_id = %s", (user_id,))
        clients = c.fetchall()
        conn.close()

        if not clients:
            st.warning("⚠️ Vous devez ajouter au moins un client avant d'ajouter des échéances.")
        else:
            client_dict = {f"{name} (ID {client_id})": client_id for client_id, name in clients}
            selected_client = st.selectbox("Select Client", list(client_dict.keys()))
            client_id = client_dict[selected_client]

            task_type = st.selectbox("Deadline Type", ["TVA", "CNSS", "IR", "IS", "Other"])
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
                st.success("✅ Échéance ajoutée avec succès !")

    elif tab == "View Deadlines":
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
            st.info("Aucune échéance trouvée.")
        else:
            with st.expander("🔍 Filter"):
                search_name = st.text_input("Search by Client Name")
                selected_status = st.selectbox("Filter by Status", ["All", "Pending", "Done"])

                if search_name:
                    df = df[df['client_name'].str.contains(search_name, case=False)]

                if selected_status != "All":
                    df = df[df['status'] == selected_status]

                df["Statut Email"] = df["email_sent"].apply(lambda x: "Envoyé ✅" if x else "Non envoyé ❌")
                df.drop(columns=["email_sent"], inplace=True)

            st.dataframe(df, use_container_width=True, hide_index=True)

            with st.expander("🗑️ Delete a Deadline"):
                deadline_ids = df["deadline_id"].tolist()
                to_delete = st.selectbox("Select deadline ID to delete", deadline_ids)

                if st.button("Delete Deadline"):
                    conn = get_connection()
                    c = conn.cursor()
                    c.execute("DELETE FROM deadlines WHERE id = %s", (to_delete,))
                    conn.commit()
                    conn.close()
                    st.success("Échéance supprimée.")
                    st.rerun()

            with st.expander("✉️ Send Individual Email"):
                deadline_ids = df["deadline_id"].tolist()
                to_email_id = st.selectbox("Select deadline ID to send email", deadline_ids, key="send_email_id")

                if st.button("Send Individual Email"):
                    try:
                        email_utils.send_individual_email(to_email_id)
                        st.success(f"Email envoyé pour l'échéance ID {to_email_id}.")
                    except Exception as e:
                        st.error(f"Échec de l'envoi de l'email: {e}")