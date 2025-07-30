import streamlit as st
from database import (
    get_all_users, get_clients_by_user_id, get_deadlines_by_client_id,
    delete_user, delete_client, delete_deadline, get_connection
)
from datetime import datetime
from email_utils import send_email
from SMS_utils import send_sms

def show_admin_panel():
    st.title("👑 Admin Dashboard")
    # Approve pending users
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT id, username, name, email, phone, registered_at FROM users WHERE approved = FALSE")
    pending_users = c.fetchall()
    conn.close()

    if pending_users:
        st.subheader("⏳ Utilisateurs en attente d'approbation")
        for user in pending_users:
            with st.expander(f"🆕 {user[2]} ({user[1]}) — {user[3]}"):
                st.write("Ce compte est en attente d'approbation.")
                st.write(f"📱 Téléphone : {user[4]}")
                if user[5]:
                    st.write(f"📅 Inscrit le : {user[5].strftime('%Y-%m-%d %H:%M:%S')}")
                else:
                    st.write("📅 Inscrit le : inconnu")
                if st.button(f"✅ Approuver {user[1]}", key=f"approve_{user[0]}"):
                    conn = get_connection()
                    c = conn.cursor()
                    c.execute("""UPDATE users SET approved = TRUE, approved_by = %s, approved_at = CURRENT_TIMESTAMP WHERE id = %s""", (st.session_state["username"], user[0]))
                    conn.commit()
                    conn.close()
                    st.success(f"L'utilisateur {user[1]} a été approuvé.")
                    subject = "Confirmation : votre compte a été approuvé ✅"
                    message = (f"Bonjour {user[1]},\n\n"
                                "Votre compte a été approuvé. Vous pouvez maintenant vous connecter et profiter de nos services.\n"

                                "Bienvenue parmi nous !\n"

                                "Cordialement,\n"
                                "L’équipe\n\n"
                                "Si vous avez des questions, n’hésitez pas à nous contacter:\n"
                                "Email:example@gmail.com\n"
                                "Téléphone: +212 6 37 15 33 78\n"
                                "Site web: www.example.com")
                    phone = user[4]
                    if phone.startswith("0"):
                        phone = "+212" + phone[1:]
                    send_email(user[3], subject, message)
                    st.success("✅ Email de confirmation envoyé.")
                    send_sms(phone, message)
                    st.success("✅ SMS de confirmation envoyé.")
                    st.rerun()
    else:
        st.info("✅ Aucun utilisateur en attente.")

    users = get_all_users()
    if not users:
        st.warning("No users found.")
        return

    for user in users:
        if user.get('approved') != True:
            continue
        with st.expander(f"👤 {user['name']} ({user['username']}) — {user['email']}"):
            # Delete User Form
            with st.form(f"delete_user_form_{user['id']}"):
                st.write("🗑️ Delete this user and all their data?")
                delete_user_submit = st.form_submit_button(f"❌ Delete User ID {user['id']}")
                if delete_user_submit:
                    delete_user(user['id'])
                    st.success("User deleted.")
                    st.rerun()

            clients = get_clients_by_user_id(user['id'])
            if not clients:
                st.info("No clients for this user.")
            else:
                for client in clients:
                    with st.expander(f"📂 Client: {client['name']} (ICE: {client['ice']})"):
                        # Delete Client Form
                        with st.form(f"delete_client_form_{client['id']}"):
                            st.write("🗑️ Delete this client and their deadlines?")
                            delete_client_submit = st.form_submit_button(f"❌ Delete Client ID {client['id']}")
                            if delete_client_submit:
                                delete_client(client['id'])
                                st.success("Client deleted.")
                                st.rerun()

                        deadlines = get_deadlines_by_client_id(client['id'])
                        if not deadlines:
                            st.info("No deadlines.")
                        else:
                            for deadline in deadlines:
                                with st.expander(f"📌 Deadline ID {deadline['id']} — {deadline['type']} due {deadline['due_date']}"):
                                    st.markdown(f"""
                                    🗓 **Type:** {deadline['type']}  
                                    🔁 **Period:** {deadline['period']}  
                                    ⏰ **Due Date:** {deadline['due_date']}  
                                    📤 **Email Sent:** {'✅' if deadline['email_sent'] else '❌'}
                                    """)

                                    # Delete Deadline Form
                                    with st.form(f"delete_deadline_form_{deadline['id']}"):
                                        delete_dl_submit = st.form_submit_button(f"❌ Delete Deadline ID {deadline['id']}")
                                        if delete_dl_submit:
                                            delete_deadline(deadline['id'])
                                            st.success("Deadline deleted.")
                                            st.rerun()
