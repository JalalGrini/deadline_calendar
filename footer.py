import streamlit as st
from dotenv import load_dotenv

load_dotenv()

my_name=load_dotenv.get("MY_NAME")
app_name=load_dotenv.get("APP_NAME")

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
            © 2025 {{app_name}} — Developed by {{my_name}}
        </footer>
        """,
        unsafe_allow_html=True
    )
