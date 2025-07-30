import streamlit as st
import pandas as pd
import io
from database import get_connection

def show_export_deadlines(user_id):
    st.subheader("📤 Export My Deadlines")
    if st.button("📥 Export Deadlines to Excel"):
        conn = get_connection()
        query = """
            SELECT 
                d.id AS ID,
                c.name AS Client,
                c.type AS Type_Client,
                d.type AS Type_Échéance,
                d.period AS Période,
                d.due_date AS "Date_d'échéance",
                d.status AS Statut,
                CASE WHEN d.email_sent THEN 'Envoyé' ELSE 'Non envoyé' END AS "Email_Envoyé"
            FROM deadlines d
            JOIN clients c ON d.client_id = c.id
            WHERE c.user_id = %s
            ORDER BY d.due_date ASC
        """
        df = pd.read_sql(query, conn, params=(user_id,))
        conn.close()

        if df.empty:
            st.warning("Aucune échéance à exporter.")
        else:
            towrite = io.BytesIO()
            df.to_excel(towrite, index=False, sheet_name="Mes Échéances")
            towrite.seek(0)
            st.download_button(
                label="📄 Download Excel",
                data=towrite,
                file_name="mes_echeances.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )