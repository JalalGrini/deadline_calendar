import streamlit as st
from database import (
    get_all_users, get_clients_by_user_id, get_deadlines_by_client_id,
    delete_user, delete_client, delete_deadline
)

def show_admin_panel():
    st.title("👑 Admin Dashboard")

    users = get_all_users()
    if not users:
        st.warning("No users found.")
        return

    for user in users:
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
