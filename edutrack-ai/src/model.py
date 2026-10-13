"""Demo risk estimator.

This first version uses transparent rules rather than pretending a model has been
trained on the synthetic demo records. Replace with a validated sklearn pipeline
after downloading and preparing a cited public dataset.
"""
def estimate_risk(student):
    attendance = float(student.get("attendance_pct", 0))
    marks = float(student.get("internal_marks", 0))
    previous = float(student.get("previous_grade", 0))
    assignment = float(student.get("assignment_score", 0))
    risk = 0.10
    if attendance < 75:
        risk += 0.25
    if attendance < 60:
        risk += 0.10
    if marks < 50:
        risk += 0.25
    elif marks < 60:
        risk += 0.15
    if previous < 50:
        risk += 0.15
    if assignment < 50:
        risk += 0.10
    return max(0.02, min(0.95, risk))

def risk_label(probability):
    if probability >= 0.60:
        return "High"
    if probability >= 0.35:
        return "Medium"
    return "Low"

def explanations(student):
    reasons = []
    if float(student.get("attendance_pct", 0)) < 75:
        reasons.append("Attendance is below the 75% reference threshold.")
    if float(student.get("internal_marks", 0)) < 50:
        reasons.append("Internal marks are low and may need review.")
    if float(student.get("previous_grade", 0)) < 50:
        reasons.append("Previous grade indicates a possible learning gap.")
    if float(student.get("assignment_score", 0)) < 50:
        reasons.append("Assignment score is low; check submission and understanding.")
    return reasons or ["No rule-based warning signals were detected in the available demo fields."]
