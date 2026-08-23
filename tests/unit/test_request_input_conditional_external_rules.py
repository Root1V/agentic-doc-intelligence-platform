"""Categories (a) request-input, (c) conditional, and (e) external-system —
one focused test per category, completing coverage of all 6 rule categories
(5 from the user's feedback plus intra-document 'self') per the Fase 0
verification plan."""

from __future__ import annotations

import pytest

from idp.validation.rules.conditional import ConditionalRule
from idp.validation.rules.external_system_rules import InsurancePolicyVerifiedExternally
from idp.validation.rules.request_input_rules import ExpectedEmployeeCodeMatches
from tests.conftest import make_context, make_document_fields


@pytest.mark.asyncio
async def test_request_input_matches_expected_employee_code():
    fields = make_document_fields("payslip", {"employee_code": "EMP001"})
    context = make_context(fields, request_payload={"expected_employee_code": "EMP001"})
    result = await ExpectedEmployeeCodeMatches().evaluate(context)
    assert result.passed


@pytest.mark.asyncio
async def test_request_input_contradicts_expected_employee_code():
    fields = make_document_fields("payslip", {"employee_code": "EMP999"})
    context = make_context(fields, request_payload={"expected_employee_code": "EMP001"})
    result = await ExpectedEmployeeCodeMatches().evaluate(context)
    assert not result.passed
    assert result.severity == "error"


@pytest.mark.asyncio
async def test_request_input_rule_omitted_when_no_expectation_given():
    fields = make_document_fields("payslip", {"employee_code": "EMP001"})
    context = make_context(fields)
    assert ExpectedEmployeeCodeMatches().applies_when(context) is False


@pytest.mark.asyncio
async def test_conditional_rule_activates_and_deactivates():
    inner = ExpectedEmployeeCodeMatches()
    always_on = ConditionalRule("cond.always_on", lambda ctx: True, inner)
    always_off = ConditionalRule("cond.always_off", lambda ctx: False, inner)

    fields = make_document_fields("payslip", {"employee_code": "EMP001"})
    context = make_context(fields, request_payload={"expected_employee_code": "EMP001"})

    assert always_on.applies_when(context) is True
    assert always_off.applies_when(context) is False

    result = await always_on.evaluate(context)
    assert result.rule_id == "cond.always_on"
    assert result.category == "conditional"


@pytest.mark.asyncio
async def test_external_system_verification_positive_and_negative():
    fields = make_document_fields("insurance_disclosure", {"policy_number": "POL-123"})
    context = make_context(fields)  # StubExternalSystemPort default: verified=False
    result = await InsurancePolicyVerifiedExternally().evaluate(context)
    assert not result.passed
    assert result.category == "external_system"
