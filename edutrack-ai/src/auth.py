import hashlib
import hmac
import streamlit as st
from src.database import get_connection

# Demo-only password hashing. For a production system, use Argon2 or bcrypt,
# HTTPS, secret-managed session/authentication infrastructure, and rate limits.
def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode("utf-8")).hexdigest()

def init_demo_users():
    demo_users = [
        ("admin", "Admin123!", "admin", None),
        ("teacher", "Teacher123!", "teacher", None),
        ("student", "Student123!", "student", "STU001"),
        ("student2", "Student123!", "student", "STU002"),
    ]
    with get_connection() as conn:
        for username, password, role, student_id in demo_users:
            conn.execute(
                """INSERT OR IGNORE INTO users(username, password_hash, role, student_id)
                   VALUES (?, ?, ?, ?)""",
                (username, hash_password(password), role, student_id),
            )

def authenticate(username: str, password: str):
    with get_connection() as conn:
        row = conn.execute(
            "SELECT username, password_hash, role, student_id FROM users WHERE username=? AND active=1",
            (username.strip(),),
        ).fetchone()
    if row and hmac.compare_digest(row["password_hash"], hash_password(password)):
        return {"username": row["username"], "role": row["role"], "student_id": row["student_id"]}
    return None

def logout():
    st.session_state.pop("user", None)
