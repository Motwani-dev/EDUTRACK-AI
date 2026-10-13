import streamlit as st
from src.auth import authenticate, init_demo_users, logout
from src.database import init_db, seed_demo_data
from src.ui import admin_page, teacher_page, student_page, login_page

st.set_page_config(page_title="EduTrack AI", page_icon="🎓", layout="wide")
init_db()
init_demo_users()
seed_demo_data()

if "user" not in st.session_state:
    login_page()
else:
    user = st.session_state["user"]
    with st.sidebar:
        st.title("🎓 EduTrack AI")
        st.caption("Student Management & Early Warning")
        st.write(f"Signed in as **{user['username']}**")
        st.write(f"Role: `{user['role'].title()}`")
        if st.button("Log out", use_container_width=True):
            logout()
            st.rerun()
        st.divider()
        st.caption("Demo application • Use synthetic data only")

    if user["role"] == "admin":
        admin_page(user)
    elif user["role"] == "teacher":
        teacher_page(user)
    else:
        student_page(user)
