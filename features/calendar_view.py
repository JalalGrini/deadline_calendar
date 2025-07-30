# calendar_view.py

import streamlit as st
from streamlit_calendar import calendar
from database import get_connection
import pandas as pd

def show_calendar_view(user_id):
    st.subheader("📅 Calendar View of Deadlines")

    conn = get_connection()
    query = """
        SELECT 
            deadlines.id AS id,
            clients.name AS client_name,
            deadlines.type AS deadline_type,
            deadlines.due_date,
            deadlines.status
        FROM deadlines
        JOIN clients ON deadlines.client_id = clients.id
        WHERE clients.user_id = %s
    """
    df = pd.read_sql(query, conn, params=(user_id,))
    conn.close()

    if df.empty:
        st.info("No deadlines found.")
        return

    # Prepare calendar events
    events = []
    for _, row in df.iterrows():
        events.append({
            "title": f"{row['client_name']} - {row['deadline_type']}",
            "start": row['due_date'].strftime("%Y-%m-%d"),
            "end": row['due_date'].strftime("%Y-%m-%d"),
            "color": "#f39c12" if row['status'] == "Pending" else "#2ecc71"
        })

    calendar_options = {
        "initialView": "dayGridMonth",
        "headerToolbar": {
            "left": "prev,next today",
            "center": "title",
            "right": "dayGridMonth,timeGridWeek"
        },
        "editable": False,
        "selectable": False,
        "height": 650
    }

    calendar(events=events, options=calendar_options)
    