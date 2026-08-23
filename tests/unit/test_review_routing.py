from __future__ import annotations

from idp.domain.envelope import Extracted
from idp.domain.schemas.payslip import PayslipSchema
from idp.review.routing import find_review_candidates
from idp.validation.base import ConfidenceMethod, RuleCategory, Severity, ValidationResult


def _payslip(confidence: float = 0.95) -> PayslipSchema:
    return PayslipSchema(
        employee_name=Extracted(value="SALAS SIGUAS, KATERIN KAROLA", confidence=confidence, source_text="x"),
        period=Extracted(value="ENERO - 2026", confidence=0.95, source_text="x"),
        gross_pay=Extracted(value=6618.00, confidence=0.98, source_text="x"),
        total_deductions=Extracted(value=2313.86, confidence=0.98, source_text="x"),
        net_pay=Extracted(value=4304.14, confidence=0.98, source_text="x"),
    )


def test_low_confidence_field_creates_review_candidate():
    instance = _payslip(confidence=0.4)
    candidates = find_review_candidates(instance, [], confidence_threshold=0.75)
    paths = {c.field_path for c in candidates}
    assert "employee_name" in paths
    reason = next(c.reason for c in candidates if c.field_path == "employee_name")
    assert reason == "low_confidence"


def test_all_high_confidence_and_no_issues_creates_no_candidates():
    instance = _payslip(confidence=0.95)
    candidates = find_review_candidates(instance, [], confidence_threshold=0.75)
    assert candidates == []


def test_validation_issue_field_creates_review_candidate_even_with_high_confidence():
    instance = _payslip(confidence=0.95)
    issue = ValidationResult(
        rule_id="self.payslip_arithmetic_consistency",
        category=RuleCategory.SELF,
        passed=False,
        severity=Severity.ERROR,
        field_path="net_pay",
        message="no coincide",
        confidence=1.0,
        confidence_method=ConfidenceMethod.DETERMINISTIC,
        explanation="x",
    )
    candidates = find_review_candidates(instance, [issue], confidence_threshold=0.75)
    paths = {c.field_path: c.reason for c in candidates}
    assert paths.get("net_pay") == "validation_issue"
