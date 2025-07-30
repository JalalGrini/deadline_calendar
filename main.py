import streamlit as st
from database import init_db, get_connection
import pandas as pd
from datetime import datetime
import email_utils
import footer
from auth import init_auth, save_user_to_db, get_user_id, custom_login
from dotenv import load_dotenv
import os
import yaml
from admin_panel import show_admin_panel
from streamlit_cookies_manager import EncryptedCookieManager
import io
from features.tva_calculator import show_tva_calculator
from features.calendar_view import show_calendar_view
from features.email_customizer import show_email_customizer

load_dotenv()

COOKIE_PASSWORD = os.getenv("COOKIE_PASSWORD")

cookies = EncryptedCookieManager(prefix="deadline_calendar_", password=COOKIE_PASSWORD)

if not cookies.ready():
    st.stop()

init_db()
st.set_page_config("📅 Deadline Calendar")
st.title("📅 Deadline Calendar Manager")

# Initialize authenticator
authenticator, config = init_auth()

# Load admin credentials from environment variables
ADMIN_USERNAME = os.getenv("ADMIN_USERNAME")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD")
ADMIN_NAME = os.getenv("MY_NAME")

# Token logic
if "auth_token" in cookies and cookies["auth_token"]:
    token = cookies["auth_token"]
    if token == "admin_token":
        st.session_state['authentication_status'] = True
        st.session_state['is_admin'] = True
        st.session_state['name'] = ADMIN_NAME
        st.session_state['username'] = ADMIN_USERNAME
    else:
        st.session_state['authentication_status'] = True
        st.session_state['is_admin'] = False
        st.session_state['username'] = token
        # ✅ Fetch full name from DB and set it
        conn = get_connection()
        c = conn.cursor()
        c.execute("SELECT name FROM users WHERE username = %s", (token,))
        row = c.fetchone()
        conn.close()
        st.session_state['name'] = row[0] if row else token  # fallback to username if no match
else:
    if 'authentication_status' not in st.session_state:
        st.session_state['authentication_status'] = None

# Authentication UI
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
                if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
                    cookies["auth_token"] = "admin_token"
                    cookies.save()
                    st.session_state['authentication_status'] = True
                    st.session_state['is_admin'] = True
                    st.session_state['name'] = ADMIN_NAME
                    st.session_state['username'] = username
                    st.success("👑 Logged in as Admin")
                    st.rerun()
                else:
                    username_db, name = custom_login(username, password)
                    if username_db:
                        cookies["auth_token"] = username_db
                        cookies.save()
                        st.session_state['authentication_status'] = True
                        st.session_state['is_admin'] = False
                        st.session_state['name'] = name
                        st.session_state['username'] = username_db
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
            phone = st.text_input("Phone Number")  # ← new
            password = st.text_input("Password", type="password")
            submit = st.form_submit_button("Register")

            if submit:
                try:
                    if not username or not name or not email or not password:
                        raise ValueError("All fields are required")
                    save_user_to_db(username, name, email, password, phone)
                    st.success("✅ Votre inscription a bien été soumise. Elle sera validée par l'administrateur.")
                except Exception as e:
                    st.error(f"Registration failed: {e}")


else:
    # Main logged-in interface

    user_id = get_user_id(st.session_state['username'])

    # Page config
    st.set_page_config(page_title="ComptaPilot", layout="wide")

    # Initialize session state
    if "feature" not in st.session_state:
        st.session_state["feature"] = "Bloc-Note Comptable"

    menu_items = [
        "Bloc-Note Comptable",
        "Calculateur de Facture (HT ➜ TTC)",
        "Exporter mes Deadlines",
        "TVA Calculator",
        "Gestion Clients & Deadlines",
        "Calendar View",
        "Customize Email"
    ]

    if st.session_state.get("is_admin"):
        menu_items.append("Admin Panel")

    # Sidebar styling
    st.markdown("""
        <style>
        .sidebar-button {
            background-color: #2c2f33;
            color: #f1f1f1;
            border: none;
            width: 100%;
            padding: 0.6em 1em;
            margin-bottom: 10px;
            text-align: left;
            border-radius: 8px;
            font-weight: 500;
            font-size: 16px;
            transition: background-color 0.3s ease;
            display: block;
        }

        .sidebar-button:hover {
            background-color: #3c4046;
            cursor: pointer;
        }

        .sidebar-button-active {
            background-color: #0066cc !important;
            color: white !important;
            border: none;
            width: 100%;
            padding: 0.6em 1em;
            margin-bottom: 10px;
            text-align: left;
            border-radius: 8px;
            font-weight: 500;
            font-size: 16px;
            display: block;
        }
        </style>
    """, unsafe_allow_html=True)

    # Render sidebar menu
    with st.sidebar:
        if "name" in st.session_state:
            st.markdown(f"<p style='color:limegreen; font-weight:bold;'>👋 Bienvenue, {st.session_state['name']}</p>", unsafe_allow_html=True)

        st.markdown("### 📂 Menu")
        for item in menu_items:
            is_active = st.session_state.feature == item
            btn_style = "sidebar-button-active" if is_active else "sidebar-button"

            if st.button(item, key=f"btn_{item}"):
                st.session_state.feature = item
                st.rerun()


    # Store selected feature (if you’re not using query params):
    feature = st.session_state["feature"]



    # Logout button always availablest.sidebar.markdown
    if st.sidebar.button("🔓 Logout"):
        cookies["auth_token"] = ""
        cookies.save()
        for key in ["authentication_status", "is_admin", "name", "username"]:
            if key in st.session_state:
                del st.session_state[key]
        st.rerun()

    # Feature views
    elif feature == "Bloc-Note Comptable":
        st.subheader("📝 Bloc-Note Comptable")

        # New note input
        new_note = st.text_area("✏️ Écrivez une nouvelle note", placeholder="Votre note ici...", height=100, max_chars=300)

        if st.button("📌 Ajouter la note"):
            if new_note.strip():
                conn = get_connection()
                c = conn.cursor()
                c.execute("INSERT INTO notes (user_id, content) VALUES (%s, %s)", (user_id, new_note))
                conn.commit()
                conn.close()
                st.success("✅ Note ajoutée !")
                st.rerun()
            else:
                st.warning("La note est vide.")

        # Display all notes
        conn = get_connection()
        c = conn.cursor()
        c.execute("SELECT id, content FROM notes WHERE user_id = %s ORDER BY id DESC", (user_id,))
        notes = c.fetchall()
        conn.close()

        if notes:
            st.markdown("### 🧾 Vos Notes")
            cols = st.columns(3)  # 3 notes per row
            for i, (note_id, content) in enumerate(notes):
                col = cols[i % 3]
                with col:
                    with st.container():
                        st.markdown(
                            f"""
                            <div style='background-color:#2c2f33; padding:10px; border-radius:10px; box-shadow:2px 2px 5px rgba(0,0,0,0.1); min-height:100px'>
                                <p style='font-size:14px;'>{content}</p>
                            </div>
                            """,
                            unsafe_allow_html=True
                        )
                        if st.button("🗑️ Supprimer", key=f"delete_{note_id}"):
                            conn = get_connection()
                            c = conn.cursor()
                            c.execute("DELETE FROM notes WHERE id = %s", (note_id,))
                            conn.commit()
                            conn.close()
                            st.success("Note supprimée.")
                            st.rerun()
        else:
            st.info("Aucune note encore.")


    elif feature == "Calculateur de Facture (HT ➜ TTC)":
        st.subheader("🧾 Calculateur de Facture (HT ➜ TTC)")
        col1, col2 = st.columns(2)
        with col1:
            ht = st.number_input("💵 Montant HT", min_value=0.0, format="%.2f", step=100.0)
        with col2:
            tva_rate = st.number_input("📊 Taux TVA (%)", min_value=0.0, max_value=100.0, value=20.0, format="%.2f")

        if ht > 0:
            tva_amount = ht * tva_rate / 100
            ttc = ht + tva_amount
            st.success(f"**Montant TVA :** {tva_amount:.2f} MAD")
            st.success(f"**Montant TTC :** {ttc:.2f} MAD")
        else:
            st.info("Entrez un montant HT pour calculer le TTC.")

    elif feature == "Exporter mes Deadlines":
        st.subheader("📤 Exporter mes Deadlines")
        if st.button("📥 Exporter Deadlines en Excel"):
            conn = get_connection()
            query = """
                SELECT 
                    d.id AS ID,
                    c.name AS Client,
                    c.type AS Type_Client,
                    d.type AS Type_Deadline,
                    d.period AS Période,
                    d.due_date AS "Date d'échéance",
                    d.status AS Statut,
                    CASE WHEN d.email_sent THEN 'Envoyé' ELSE 'Non envoyé' END AS "Email Envoyé"
                FROM deadlines d
                JOIN clients c ON d.client_id = c.id
                WHERE c.user_id = %s
                ORDER BY d.due_date ASC
            """
            df = pd.read_sql(query, conn, params=(user_id,))
            conn.close()

            if df.empty:
                st.warning("Aucune deadline à exporter.")
            else:
                towrite = io.BytesIO()
                df.to_excel(towrite, index=False, sheet_name="Mes Deadlines")
                towrite.seek(0)
                st.download_button(
                    label="📄 Télécharger Excel",
                    data=towrite,
                    file_name="mes_deadlines.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )

    elif feature == "TVA Calculator":
        show_tva_calculator()

    elif feature == "Gestion Clients & Deadlines":
        tab = st.radio("Gestion:", ["Add Client", "Add Deadline", "View Deadlines"])

        if tab == "Add Client":
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
                        INSERT INTO clients (user_id, name, ice, if_number, email, phone, type)
                        VALUES (%s, %s, %s, %s, %s, %s, %s)
                    """, (user_id, name, ice, if_number, email, phone, client_type))
                    conn.commit()
                    conn.close()
                    st.success(f"Client '{name}' added successfully ✅")

        elif tab == "Add Deadline":
            st.subheader("📌 Add Deadline for a Client")
            conn = get_connection()
            c = conn.cursor()
            c.execute("SELECT id, name FROM clients WHERE user_id = %s", (user_id,))
            clients = c.fetchall()
            conn.close()

            if not clients:
                st.warning("⚠️ You must add at least one client before adding deadlines.")
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
                    st.success("✅ Deadline added successfully!")

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
                st.info("No deadlines found.")
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
                        st.success("Deadline deleted.")
                        st.rerun()

                with st.expander("✉️ Send Individual Email"):
                    deadline_ids = df["deadline_id"].tolist()
                    to_email_id = st.selectbox("Select deadline ID to send email", deadline_ids, key="send_email_id")

                    if st.button("Send Individual Email"):
                        try:
                            email_utils.send_individual_email(to_email_id)
                            st.success(f"Email sent for deadline ID {to_email_id}.")
                        except Exception as e:
                            st.error(f"Failed to send email: {e}")
    elif feature == "Calendar View":
        show_calendar_view(user_id)
    elif feature == "Customize Email":
        show_email_customizer(user_id)
    elif feature == "Admin Panel" and st.session_state['is_admin']:
        show_admin_panel()

footer.footer()