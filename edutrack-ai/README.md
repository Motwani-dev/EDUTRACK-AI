# EduTrack AI — Student Management & Early Warning System

A Streamlit demo app for student records, marks, attendance, academic analytics, and transparent rule-based support indicators.

## Features
- Admin, teacher, and student demo roles
- Student CRUD operations
- Marks entry and assessment reports
- CSV import/export
- Academic charts
- Transparent rule-based early-warning demo
- SQLite persistence for local development

## Run locally
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

## Demo accounts
- Admin: `admin` / `Admin123!`
- Teacher: `teacher` / `Teacher123!`
- Student: `student` / `Student123!`
- Student 2: `student2` / `Student123!`

These credentials and the authentication implementation are for a classroom prototype only. Do not use them for sensitive or real student data. Before production use, replace the demo authentication with a proper authentication provider, use strong password hashing, protect secrets, enforce server-side permissions, and use a managed persistent database.

## Machine learning status
The included early-warning calculation is a transparent **rule-based demonstration**, not a trained or validated machine-learning model. To complete the advanced ML requirement, select and cite a public dataset, define a prediction target and prediction time, prevent target leakage, train a scikit-learn pipeline, evaluate it on held-out data, and document limitations before presenting predictions as model output.

## Dataset
No external dataset is bundled. The application seeds clearly synthetic demonstration records. Cite any public dataset you download and comply with its license/terms.

## Deployment
Push this repository to GitHub, open Streamlit Community Cloud, select the repository/branch and `app.py`, and deploy. For multi-user cloud use, replace local SQLite storage with a managed database; local files may not be durable across restarts/redeployments.
