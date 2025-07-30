import streamlit as st
from database import get_connection

def show_notes(user_id):
    st.subheader("📝 Accounting Notes")

    # New note input
    new_note = st.text_area("✏️ Write a new note", placeholder="Your note here...", height=100, max_chars=300)

    if st.button("📌 Add Note"):
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
                    if st.button("🗑️ Delete", key=f"delete_{note_id}"):
                        conn = get_connection()
                        c = conn.cursor()
                        c.execute("DELETE FROM notes WHERE id = %s", (note_id,))
                        conn.commit()
                        conn.close()
                        st.success("Note supprimée.")
                        st.rerun()
    else:
        st.info("Aucune note encore.")