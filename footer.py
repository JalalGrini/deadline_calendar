import streamlit as st

def footer():
    st.markdown(
        """
        <style>
        footer {
            visibility: visible;
            position: fixed;
            left: 0;
            bottom: 0;
            width: 100%;
            background-color: #f1f1f1;
            text-align: center;
            padding: 10px 0;
            font-size: 14px;
            color: #555;
        }
        </style>
        <footer>
            © 2025 Comptable Solutions — Developed by Jalal Grini
        </footer>
        """,
        unsafe_allow_html=True
    )
