import streamlit as st
from database import get_connection
import email_utils
import SMS_utils
from datetime import datetime, timedelta
import streamlit.components.v1 as components
import time

def show_email_customizer(user_id):
    st.subheader("✉️ Customize Email and SMS Reminders")

    # Available variables
    available_variables = [
        "{client_name}", "{client_email}", "{client_phone}", "{client_type}",
        "{ice}", "{if_number}", "{deadline_type}", "{period}", "{due_date}",
        "{status}"
    ]

    # Initialize session state
    if 'email_message_template' not in st.session_state:
        st.session_state['email_message_template'] = (
            "Bonjour {client_name},\n\n"
            "Votre échéance {deadline_type} ({period}) est prévue pour le {due_date}.\n"
            "Merci de prendre les mesures nécessaires.\n\n"
            "Cordialement,\nL'équipe"
        )
    if 'sms_message_template' not in st.session_state:
        st.session_state['sms_message_template'] = (
            "Bonjour {client_name}, votre échéance {deadline_type} ({period}) est due le {due_date}. Merci."
        )
    if 'variable_inserted' not in st.session_state:
        st.session_state['variable_inserted'] = False

    # Load saved templates
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
        SELECT id, email_message, sms_message, email_subject, deadline_type, client_id, days_before, created_at
        FROM message_templates
        WHERE user_id = %s
        ORDER BY created_at DESC
    """, (user_id,))
    templates = c.fetchall()
    conn.close()

    # Display saved templates
    if templates:
        st.markdown("### 📋 Saved Templates")
        for template in templates:
            template_id, email_msg, sms_msg, subject, dl_type, client_id, days, created = template
            with st.expander(f"Template ID {template_id} — {dl_type or 'All'} ({created.strftime('%Y-%m-%d %H:%M')})"):
                st.write(f"**Email Subject:** {subject or 'N/A'}")
                st.write(f"**Email Message:** {email_msg or 'N/A'}")
                st.write(f"**SMS Message:** {sms_msg or 'N/A'}")
                st.write(f"**Days Before:** {days}")
                st.write(f"**Deadline Type:** {dl_type or 'All'}")
                conn = get_connection()
                c = conn.cursor()
                c.execute("SELECT name FROM clients WHERE id = %s", (client_id,) if client_id else (None,))
                client_name = c.fetchone()
                conn.close()
                st.write(f"**Client:** {client_name[0] if client_name else 'All Clients'}")
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("Load Template", key=f"load_{template_id}"):
                        st.session_state['email_message_template'] = email_msg or ""
                        st.session_state['sms_message_template'] = sms_msg or ""
                        st.session_state['email_subject'] = subject or "Rappel d'échéance personnalisé"
                        st.session_state['days_before'] = days or 1
                        st.session_state['deadline_type'] = dl_type or "All"
                        st.session_state['client_id'] = client_id
                        st.rerun()
                with col2:
                    if st.button("Delete Template", key=f"delete_{template_id}"):
                        conn = get_connection()
                        c = conn.cursor()
                        c.execute("DELETE FROM message_templates WHERE id = %s AND user_id = %s", (template_id, user_id))
                        conn.commit()
                        conn.close()
                        st.success(f"Template ID {template_id} deleted.")
                        st.rerun()

    # Variable insertion controls
    st.markdown("### 🛠️ Create or Edit Template")
    st.radio("Insert Variable Into:", ["Email", "SMS"], key="variable_target", horizontal=True)
    cols = st.columns(4)
    for i, var in enumerate(available_variables):
        with cols[i % 4]:
            if st.button(var, key=f"insert_var_{var}"):
                st.session_state['selected_variable'] = var
                st.session_state['variable_inserted'] = True

    # Form for customizing email and SMS
    with st.form("custom_email_sms_form", clear_on_submit=False):
        # Email message input
        email_message_template = st.text_area(
            "Email Message Template",
            value=st.session_state['email_message_template'],
            placeholder="Enter your email message here with variables like {client_name}, {deadline_type}, etc.",
            height=200,
            key="email_message_input"
        )

        # SMS message input
        sms_message_template = st.text_area(
            "SMS Message Template",
            value=st.session_state['sms_message_template'],
            placeholder="Enter your SMS message here with variables like {client_name}, {deadline_type}, etc.",
            height=100,
            key="sms_message_input"
        )

        # Handle variable insertion
        if st.session_state.get('variable_inserted', False):
            var = st.session_state['selected_variable']
            target = st.session_state['variable_target']
            textarea_id = "email_message_input" if target == "Email" else "sms_message_input"
            components.html(
                f"""
                <script>
                (function() {{
                    const textarea = document.getElementById('{textarea_id}');
                    if (textarea) {{
                        const startPos = textarea.selectionStart;
                        const endPos = textarea.selectionEnd;
                        const value = textarea.value;
                        const newValue = value.substring(0, startPos) + '{var}' + value.substring(endPos);
                        textarea.value = newValue;
                        const newPos = startPos + '{var}'.length;
                        textarea.selectionStart = newPos;
                        textarea.selectionEnd = newPos;
                        const event = new Event('input', {{ bubbles: true }});
                        textarea.dispatchEvent(event);
                    }}
                }})();
                </script>
                """,
                height=0
            )
            if target == "Email":
                st.session_state['email_message_template'] = email_message_template
            else:
                st.session_state['sms_message_template'] = sms_message_template
            st.session_state['variable_inserted'] = False
            if 'selected_variable' in st.session_state:
                del st.session_state['selected_variable']

        # Update session state for manual edits
        if email_message_template != st.session_state['email_message_template']:
            st.session_state['email_message_template'] = email_message_template
        if sms_message_template != st.session_state['sms_message_template']:
            st.session_state['sms_message_template'] = sms_message_template

        # Days before deadline
        days_before = st.number_input(
            "Days Before Deadline",
            min_value=0,
            value=st.session_state.get('days_before', 1),
            step=1,
            key="days_before_input"
        )

        # Filter by deadline type
        deadline_types = ["All", "TVA", "CNSS", "IR", "IS", "Other"]
        selected_deadline_type = st.selectbox(
            "Filter by Deadline Type",
            deadline_types,
            index=deadline_types.index(st.session_state.get('deadline_type', "All")),
            key="deadline_type_input"
        )

        # Filter by client
        conn = get_connection()
        c = conn.cursor()
        c.execute("SELECT id, name FROM clients WHERE user_id = %s", (user_id,))
        clients = c.fetchall()
        conn.close()
        client_dict = {"All Clients": None} | {f"{name} (ID {client_id})": client_id for client_id, name in clients}
        selected_client = st.selectbox(
            "Filter by Client",
            list(client_dict.keys()),
            index=list(client_dict.values()).index(st.session_state.get('client_id', None)) if st.session_state.get('client_id') in client_dict.values() else 0,
            key="client_input"
        )

        # Subject (for email only)
        subject = st.text_input(
            "Email Subject",
            value=st.session_state.get('email_subject', "Rappel d'échéance personnalisé"),
            key="subject_input"
        )

        # Submit button
        submit_button = st.form_submit_button("Send and Save Template")
        if submit_button:
            if not email_message_template.strip() and not sms_message_template.strip():
                st.error("At least one message template (Email or SMS) must not be empty.")
                return

            # Save template to database
            conn = get_connection()
            c = conn.cursor()
            c.execute("""
                INSERT INTO message_templates (user_id, email_message, sms_message, email_subject, deadline_type, client_id, days_before)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (
                user_id,
                email_message_template.strip() or None,
                sms_message_template.strip() or None,
                subject.strip() or None,
                selected_deadline_type if selected_deadline_type != "All" else None,
                client_dict[selected_client],
                days_before
            ))
            conn.commit()
            conn.close()
            st.success("Template saved successfully.")
            time.sleep(1)
            st.rerun()  # Rerun to clear form fields
            # Send emails and SMS
            query = """
                SELECT c.name, c.email, c.phone, c.type, c.ice, c.if_number,
                       d.type AS deadline_type, d.period, d.due_date, d.status,
                       d.email_sent, d.sms_sent, d.id AS deadline_id
                FROM deadlines d
                JOIN clients c ON d.client_id = c.id
                WHERE d.status = 'Pending' AND c.user_id = %s
            """
            params = [user_id]
            if selected_deadline_type != "All":
                query += " AND d.type = %s"
                params.append(selected_deadline_type)
            if client_dict[selected_client]:
                query += " AND c.id = %s"
                params.append(client_dict[selected_client])
            if days_before > 0:
                reminder_date = (datetime.now() + timedelta(days=days_before)).strftime("%Y-%m-%d")
                query += " AND d.due_date = %s"
                params.append(reminder_date)

            conn = get_connection()
            c = conn.cursor()
            c.execute(query, params)
            rows = c.fetchall()
            conn.close()

            if not rows:
                st.warning("No matching deadlines found for the selected criteria.")
                return

            for row in rows:
                client_name, client_email, client_phone, client_type, ice, if_number, deadline_type, period, due_date, status, email_sent, sms_sent, deadline_id = row
                
                try:
                    email_message = email_message_template.format(
                        client_name=client_name,
                        client_email=client_email,
                        client_phone=client_phone or "N/A",
                        client_type=client_type or "N/A",
                        ice=ice or "N/A",
                        if_number=if_number or "N/A",
                        deadline_type=deadline_type,
                        period=period,
                        due_date=due_date,
                        status=status
                    ) if email_message_template.strip() else None
                    
                    sms_message = sms_message_template.format(
                        client_name=client_name,
                        client_email=client_email,
                        client_phone=client_phone or "N/A",
                        client_type=client_type or "N/A",
                        ice=ice or "N/A",
                        if_number=if_number or "N/A",
                        deadline_type=deadline_type,
                        period=period,
                        due_date=due_date,
                        status=status
                    ) if sms_message_template.strip() else None
                except KeyError as e:
                    st.error(f"Invalid variable in message template: {e}")
                    continue

                if email_message and email_utils.is_valid_email(client_email):
                    try:
                        email_utils.send_email(client_email, subject, email_message)
                        email_utils.log_email_sent(user_id, deadline_id)
                        conn = get_connection()
                        c = conn.cursor()
                        c.execute("UPDATE deadlines SET email_sent = TRUE WHERE id = %s", (deadline_id,))
                        conn.commit()
                        conn.close()
                        st.success(f"Email sent to {client_name} ({client_email})")
                    except Exception as e:
                        st.error(f"Failed to send email to {client_email}: {e}")

                if sms_message and client_phone:
                    if client_phone.startswith("0"):
                        client_phone = "+212" + client_phone[1:]
                    if client_phone.startswith("+"):
                        try:
                            SMS_utils.send_sms(client_phone, sms_message)
                            conn = get_connection()
                            c = conn.cursor()
                            c.execute(
                                "INSERT INTO sms_logs (user_id, deadline_id, phone, message) VALUES (%s, %s, %s, %s)",
                                (user_id, deadline_id, client_phone, sms_message)
                            )
                            c.execute("UPDATE deadlines SET sms_sent = TRUE WHERE id = %s", (deadline_id,))
                            conn.commit()
                            conn.close()
                            st.success(f"SMS sent to {client_name} ({client_phone})")
                        except Exception as e:
                            st.error(f"Failed to send SMS to {client_phone}: {e}")
                    else:
                        st.warning(f"Skipping invalid phone: {client_phone}")

            