import streamlit as st
from database import init_db, get_connection
from auth import init_auth, save_user_to_db, get_user_id, custom_login
from dotenv import load_dotenv
import os
from admin_panel import show_admin_panel
from streamlit_cookies_manager import EncryptedCookieManager
from features.tva_calculator import show_tva_calculator
from features.calendar_view import show_calendar_view
from features.email_customizer import show_email_customizer
from features.notes import show_notes
from features.invoice_calculator import show_invoice_calculator
from features.export_deadlines import show_export_deadlines
from features.client_deadline_manager import show_client_deadline_manager
import footer

load_dotenv()

COOKIE_PASSWORD = os.getenv("COOKIE_PASSWORD")

cookies = EncryptedCookieManager(prefix="deadline_calendar_", password=COOKIE_PASSWORD)

if not cookies.ready():
    st.stop()

init_db()
st.set_page_config("📅 ComptaPilot")
st.title("📅 ComptaPilot")

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
            phone = st.text_input("Phone Number")
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
        st.session_state["feature"] = "Accounting Notes"

    menu_items = [
        "Accounting Notes",
        "Invoice Calculator (Excl. VAT ➜ Incl. VAT)",
        "Export My Deadlines",
        "VAT Calculator",
        "Client & Deadline Management",
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

    # Store selected feature
    feature = st.session_state["feature"]

    # Logout button always available
    if st.sidebar.button("🔓 Logout"):
        cookies["auth_token"] = ""
        cookies.save()
        for key in ["authentication_status", "is_admin", "name", "username"]:
            if key in st.session_state:
                del st.session_state[key]
        st.rerun()

    # Feature views
    if feature == "Accounting Notes":
        show_notes(user_id)
    elif feature == "Invoice Calculator (Excl. VAT ➜ Incl. VAT)":
        show_invoice_calculator()
    elif feature == "Export My Deadlines":
        show_export_deadlines(user_id)
    elif feature == "VAT Calculator":
        show_tva_calculator()
    elif feature == "Client & Deadline Management":
        show_client_deadline_manager(user_id)
    elif feature == "Calendar View":
        show_calendar_view(user_id)
    elif feature == "Customize Email":
        show_email_customizer(user_id)
    elif feature == "Admin Panel" and st.session_state['is_admin']:
        show_admin_panel()

footer.footer()