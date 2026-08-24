"""Unit tests for the CEL-backed generic rule (validation/rules/generic.py)
and the compile wrapper (validation/cel.py) — no DB, no LLM. Uses the same
gross_pay/total_deductions/net_pay values as test_self_validators.py so a
future reader isn't inventing new 'trust me' fixture numbers."""

from __future__ import annotations

import uuid

import pytest

from idp.persistence.models import ValidationRuleDefinition
from idp.validation.cel import CelCompileError, compile_expression
from idp.validation.rules.generic import DataDrivenRule
from tests.conftest import make_context, make_document_fields


def _row(**overrides) -> ValidationRuleDefinition:
    defaults = dict(
        id=uuid.uuid4(),
        kind="cel",
        rule_id="custom.test_rule",
        category="self",
        document_type="payslip",
        field_path="net_pay",
        condition_cel=(
            "has(doc.gross_pay) && has(doc.total_deductions) && has(doc.net_pay) "
            "? (doc.gross_pay - doc.total_deductions - doc.net_pay < 0.011 "
            "&& doc.gross_pay - doc.total_deductions - doc.net_pay > -0.011) : true"
        ),
        applies_when_cel=None,
        severity="error",
        message_pass="ok",
        message_fail="fail",
        status="active",
    )
    defaults.update(overrides)
    return ValidationRuleDefinition(**defaults)


@pytest.mark.asyncio
async def test_data_driven_rule_passes_when_condition_true():
    fields = make_document_fields("payslip", {"gross_pay": 6618.00, "total_deductions": 2313.86, "net_pay": 4304.14})
    rule = DataDrivenRule(_row())
    result = await rule.evaluate(make_context(fields))
    assert result.passed


@pytest.mark.asyncio
async def test_data_driven_rule_fails_when_condition_false():
    fields = make_document_fields("payslip", {"gross_pay": 6618.00, "total_deductions": 2313.86, "net_pay": 1.00})
    rule = DataDrivenRule(_row())
    result = await rule.evaluate(make_context(fields))
    assert not result.passed
    assert result.severity == "error"
    assert result.field_path == "net_pay"


@pytest.mark.asyncio
async def test_data_driven_rule_gracefully_skips_on_missing_field():
    # has() correctly gates a genuinely-missing field — condition itself
    # evaluates via the has()-guard rather than raising.
    fields = make_document_fields("payslip", {})
    rule = DataDrivenRule(_row())
    result = await rule.evaluate(make_context(fields))
    assert result.passed


@pytest.mark.asyncio
async def test_data_driven_rule_falls_back_gracefully_without_has_guard():
    # No has() guard at all — referencing an absent field raises
    # CelEvaluationError at runtime; evaluate() must catch it and degrade
    # to a passed=True "regla omitida" result, not propagate.
    fields = make_document_fields("payslip", {})
    rule = DataDrivenRule(_row(condition_cel="doc.gross_pay > 0.0"))
    result = await rule.evaluate(make_context(fields))
    assert result.passed
    assert "omitida" in result.message


def test_applies_when_gates_on_document_type():
    rule = DataDrivenRule(_row(document_type="insurance_disclosure"))
    fields = make_document_fields("payslip", {})
    assert rule.applies_when(make_context(fields)) is False


def test_applies_when_cel_gate():
    fields_over = make_document_fields("payslip", {"gross_pay": 5000.0})
    fields_under = make_document_fields("payslip", {"gross_pay": 100.0})
    rule = DataDrivenRule(_row(document_type="payslip", applies_when_cel="has(doc.gross_pay) && doc.gross_pay > 1000.0"))
    assert rule.applies_when(make_context(fields_over)) is True
    assert rule.applies_when(make_context(fields_under)) is False


@pytest.mark.asyncio
async def test_reference_data_category_precomputes_employee_code_exists():
    fields = make_document_fields("payslip", {"employee_code": "011858"})
    rule = DataDrivenRule(
        _row(
            category="reference_data",
            field_path="employee_code",
            condition_cel="reference_data.employee_code_exists",
        )
    )
    context = make_context(fields, reference_employees={"011858": "Victor Espiritu"})
    result = await rule.evaluate(context)
    assert result.passed


@pytest.mark.asyncio
async def test_reference_data_category_fails_when_code_not_found():
    fields = make_document_fields("payslip", {"employee_code": "999999"})
    rule = DataDrivenRule(
        _row(
            category="reference_data",
            field_path="employee_code",
            condition_cel="reference_data.employee_code_exists",
        )
    )
    context = make_context(fields, reference_employees={"011858": "Victor Espiritu"})
    result = await rule.evaluate(context)
    assert not result.passed


def test_compile_expression_raises_on_invalid_cel():
    with pytest.raises(CelCompileError):
        compile_expression("doc.gross_pay ++ 1 ===")


def test_compile_expression_succeeds_on_valid_cel():
    compile_expression("doc.gross_pay > doc.net_pay")  # must not raise
