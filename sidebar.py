import streamlit as st

def render_sidebar_menu(menu_items, is_admin, cookies):
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

    with st.sidebar:
        st.markdown("### 📂 Menu")
        for item in menu_items:
            is_active = st.session_state.feature == item
            btn_style = "sidebar-button-active" if is_active else "sidebar-button"
            if st.button(item, key=f"btn_{item}"):
                st.session_state.feature = item

        if st.sidebar.button("🔓 Logout"):
            cookies["auth_token"] = ""
            cookies.save()
            keys_to_del = ["authentication_status", "is_admin", "name", "username", "feature"]
            for key in keys_to_del:
                if key in st.session_state:
                    del st.session_state[key]
            st.rerun()
