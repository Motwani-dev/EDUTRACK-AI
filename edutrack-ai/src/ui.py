import io
import pandas as pd
import plotly.express as px
import streamlit as st
from src.auth import authenticate
from src.database import all_students, save_student, delete_student, add_mark, get_marks
from src.model import estimate_risk, risk_label, explanations

DEPARTMENTS = ["Computer Engineering", "Information Technology", "Electronics", "Mechanical", "Civil"]

def login_page():
    st.title("🎓 EduTrack AI")
    st.subheader("Student Management & Early Warning System")
    st.write("Manage academic records, explore performance and identify students who may benefit from support.")
    with st.form("login_form"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        submitted = st.form_submit_button("Log in", use_container_width=True)
    if submitted:
        user = authenticate(username, password)
        if user:
            st.session_state["user"] = user
            st.rerun()
        else:
            st.error("Invalid username or password.")
    with st.expander("Demo login accounts"):
        st.markdown("""
        - **Admin:** `admin` / `Admin123!`
        - **Teacher:** `teacher` / `Teacher123!`
        - **Student:** `student` / `Student123!`
        - **Second student:** `student2` / `Student123!`

        These are demonstration credentials. Change them and use a proper authentication service before any real deployment.
        """)

def _metrics(df):
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Students", len(df))
    c2.metric("Average internal marks", f"{df['internal_marks'].mean():.1f}%" if len(df) else "—")
    c3.metric("Average attendance", f"{df['attendance_pct'].mean():.1f}%" if len(df) else "—")
    if len(df):
        high = sum(estimate_risk(row) >= .60 for row in df.to_dict("records"))
    else:
        high = 0
    c4.metric("High-risk reviews", high)

def _charts(df):
    if df.empty:
        st.info("Add student records to display analytics.")
        return
    left, right = st.columns(2)
    with left:
        fig = px.histogram(df, x="internal_marks", nbins=10, title="Internal marks distribution",
                           labels={"internal_marks": "Internal marks (%)"})
        st.plotly_chart(fig, use_container_width=True)
    with right:
        fig = px.scatter(df, x="attendance_pct", y="internal_marks", color="department",
                         hover_name="name", title="Attendance vs internal marks",
                         labels={"attendance_pct": "Attendance (%)", "internal_marks": "Internal marks (%)"})
        st.plotly_chart(fig, use_container_width=True)
    dept = df.groupby("department", as_index=False)["internal_marks"].mean()
    fig = px.bar(dept, x="department", y="internal_marks", title="Average marks by department",
                 labels={"department": "Department", "internal_marks": "Average marks (%)"})
    st.plotly_chart(fig, use_container_width=True)

def _student_form(prefix, initial=None):
    initial = initial or {}
    with st.form(prefix):
        col1, col2 = st.columns(2)
        sid = col1.text_input("Student ID", value=initial.get("student_id", ""))
        name = col2.text_input("Full name", value=initial.get("name", ""))
        department = col1.selectbox("Department", DEPARTMENTS,
            index=DEPARTMENTS.index(initial.get("department", DEPARTMENTS[0])) if initial.get("department", DEPARTMENTS[0]) in DEPARTMENTS else 0)
        semester = col2.number_input("Semester", min_value=1, max_value=12, value=int(initial.get("semester", 5)))
        attendance = col1.number_input("Attendance (%)", min_value=0.0, max_value=100.0, value=float(initial.get("attendance_pct", 75.0)))
        previous = col2.number_input("Previous grade (%)", min_value=0.0, max_value=100.0, value=float(initial.get("previous_grade", 60.0)))
        marks = col1.number_input("Internal marks (%)", min_value=0.0, max_value=100.0, value=float(initial.get("internal_marks", 60.0)))
        assignment = col2.number_input("Assignment score (%)", min_value=0.0, max_value=100.0, value=float(initial.get("assignment_score", 60.0)))
        study = col1.number_input("Study-time feature (dataset units)", min_value=0.0, max_value=20.0, value=float(initial.get("study_time", 2.0)))
        saved = st.form_submit_button("Save student", use_container_width=True)
    if saved:
        try:
            save_student({"student_id": sid, "name": name, "department": department, "semester": semester,
                          "attendance_pct": attendance, "previous_grade": previous, "internal_marks": marks,
                          "assignment_score": assignment, "study_time": study}, original_id=initial.get("student_id"))
            st.success("Student record saved.")
            st.rerun()
        except Exception as exc:
            st.error(f"Could not save record: {exc}")

def admin_page(user):
    st.title("Admin dashboard")
    st.caption("Manage demo records and review whole-class analytics.")
    df = all_students()
    _metrics(df)
    tab1, tab2, tab3, tab4 = st.tabs(["Overview", "Students", "Marks", "Data import/export"])
    with tab1:
        _charts(df)
        st.subheader("Early warning review list")
        if not df.empty:
            risk_df = df.copy()
            risk_df["risk_probability"] = risk_df.apply(lambda r: estimate_risk(r.to_dict()), axis=1)
            risk_df["risk_level"] = risk_df["risk_probability"].apply(risk_label)
            risk_df["risk_probability"] = (risk_df["risk_probability"] * 100).round(1)
            st.dataframe(risk_df[["student_id","name","attendance_pct","internal_marks","risk_probability","risk_level"]],
                         use_container_width=True, hide_index=True)
    with tab2:
        st.subheader("Add a student")
        _student_form("add_student")
        st.subheader("Edit or delete a student")
        if not df.empty:
            chosen = st.selectbox("Choose student", df["student_id"].tolist(), format_func=lambda x: f"{x} — {df.loc[df.student_id == x, 'name'].iloc[0]}")
            record = df.loc[df.student_id == chosen].iloc[0].to_dict()
            with st.expander("Edit selected record"):
                _student_form("edit_student", record)
            if st.button("Delete selected student", type="secondary"):
                delete_student(chosen)
                st.success("Student deleted.")
                st.rerun()
            st.dataframe(df, use_container_width=True, hide_index=True)
    with tab3:
        _marks_page(df)
    with tab4:
        _import_export(df)

def teacher_page(user):
    st.title("Teacher dashboard")
    st.caption("Review student progress, enter assessment scores and identify students for follow-up.")
    df = all_students()
    _metrics(df)
    t1, t2, t3 = st.tabs(["Class analytics", "Enter marks", "Early warning"])
    with t1:
        _charts(df)
        st.dataframe(df[["student_id","name","department","semester","attendance_pct","internal_marks","assignment_score"]],
                     use_container_width=True, hide_index=True)
    with t2:
        _marks_page(df)
    with t3:
        if not df.empty:
            for row in df.to_dict("records"):
                p = estimate_risk(row)
                if p >= .35:
                    with st.expander(f"{row['student_id']} — {row['name']} | {risk_label(p)} review"):
                        st.write(f"Rule-based demo risk estimate: **{p:.0%}**")
                        for reason in explanations(row):
                            st.write(f"- {reason}")
                        st.info("Use this as a prompt for human review, not as a final judgment about the student.")

def student_page(user):
    st.title("My student portal")
    student_id = user.get("student_id")
    df = all_students()
    own = df[df["student_id"] == student_id]
    if own.empty:
        st.warning("No student record is linked to this account. Ask the admin to link your account.")
        return
    row = own.iloc[0].to_dict()
    c1, c2, c3 = st.columns(3)
    c1.metric("Attendance", f"{row['attendance_pct']:.1f}%")
    c2.metric("Internal marks", f"{row['internal_marks']:.1f}%")
    c3.metric("Assignment score", f"{row['assignment_score']:.1f}%")
    st.subheader(f"Welcome, {row['name']}")
    st.caption(f"{row['department']} · Semester {row['semester']}")
    own_marks = get_marks(student_id)
    st.subheader("My assessment records")
    if own_marks.empty:
        st.info("No assessment records yet.")
    else:
        st.dataframe(own_marks[["subject","assessment","score","max_score","percentage"]],
                     use_container_width=True, hide_index=True)
        fig = px.bar(own_marks, x="subject", y="percentage", color="assessment",
                     title="My subject-wise scores", labels={"percentage":"Score (%)"})
        st.plotly_chart(fig, use_container_width=True)
    st.subheader("Personal improvement suggestions")
    reasons = explanations(row)
    for reason in reasons:
        st.write(f"- {reason}")
    p = estimate_risk(row)
    st.caption(f"Rule-based demo indicator: {risk_label(p)}. This is not a validated machine-learning prediction.")
    if p >= .35:
        st.info("Consider discussing a study plan with your teacher and reviewing the subjects where you need help.")

def _marks_page(df):
    st.subheader("Record or update a mark")
    if df.empty:
        st.info("Add students first.")
        return
    with st.form("mark_form"):
        sid = st.selectbox("Student", df["student_id"].tolist(), format_func=lambda x: f"{x} — {df.loc[df.student_id == x, 'name'].iloc[0]}")
        subject = st.selectbox("Subject", ["Python for Data Science","Database Management","Computer Networks","Mathematics","Other"])
        assessment = st.selectbox("Assessment", ["Internal 1","Internal 2","Assignment","Practical","Final"])
        max_score = st.number_input("Maximum score", min_value=1.0, max_value=1000.0, value=100.0)
        score = st.number_input("Score", min_value=0.0, max_value=1000.0, value=70.0)
        submitted = st.form_submit_button("Save mark")
    if submitted:
        try:
            add_mark(sid, subject, assessment, score, max_score)
            st.success("Mark saved.")
            st.rerun()
        except Exception as exc:
            st.error(str(exc))
    st.subheader("Assessment records")
    marks = get_marks()
    if marks.empty:
        st.info("No marks recorded.")
    else:
        st.dataframe(marks, use_container_width=True, hide_index=True)

def _import_export(df):
    st.subheader("Export student records")
    st.download_button("Download students as CSV", df.to_csv(index=False).encode("utf-8"),
                       file_name="edutrack_students.csv", mime="text/csv")
    st.subheader("Import students from CSV")
    st.caption("Required columns: student_id, name. Optional columns can be left blank and receive safe defaults.")
    uploaded = st.file_uploader("Upload CSV", type=["csv"])
    if uploaded is not None and st.button("Validate and import CSV"):
        try:
            incoming = pd.read_csv(uploaded)
            required = {"student_id", "name"}
            if not required.issubset(incoming.columns):
                st.error("CSV must include student_id and name columns.")
                return
            imported = 0
            for _, r in incoming.iterrows():
                data = {
                    "student_id": str(r["student_id"]).strip(),
                    "name": str(r["name"]).strip(),
                    "department": str(r.get("department", DEPARTMENTS[0])),
                    "semester": int(r.get("semester", 5)),
                    "attendance_pct": float(r.get("attendance_pct", 75)),
                    "previous_grade": float(r.get("previous_grade", 60)),
                    "internal_marks": float(r.get("internal_marks", 60)),
                    "assignment_score": float(r.get("assignment_score", 60)),
                    "study_time": float(r.get("study_time", 2)),
                }
                save_student(data)
                imported += 1
            st.success(f"Imported or updated {imported} student records.")
            st.rerun()
        except Exception as exc:
            st.error(f"Import failed. Check CSV values. Details: {exc}")
