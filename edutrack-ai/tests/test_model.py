from src.model import estimate_risk, risk_label, explanations

def test_low_risk_example():
    student = {"attendance_pct": 95, "internal_marks": 85, "previous_grade": 80, "assignment_score": 90}
    p = estimate_risk(student)
    assert 0 <= p <= 1
    assert risk_label(p) == "Low"

def test_high_risk_example():
    student = {"attendance_pct": 40, "internal_marks": 30, "previous_grade": 35, "assignment_score": 40}
    p = estimate_risk(student)
    assert p >= 0.60
    assert explanations(student)
