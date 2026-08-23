"""Category (d): existence-in-database checks, exact (by code) and fuzzy
(by name) — both paths, using ``InMemoryReferenceDataPort`` (Phase 0's
test double, no Postgres needed for this test)."""

from __future__ import annotations

import pytest

from idp.validation.rules.reference_data_rules import EmployeeCodeExistsInReferenceData, EmployeeNameExistsInReferenceData
from tests.conftest import make_context, make_document_fields


@pytest.mark.asyncio
async def test_employee_code_exists():
    fields = make_document_fields("payslip", {"employee_code": "EMP001"})
    context = make_context(fields, reference_employees={"EMP001": "Salas Siguas, Katerin Karola"})
    result = await EmployeeCodeExistsInReferenceData().evaluate(context)
    assert result.passed


@pytest.mark.asyncio
async def test_employee_code_does_not_exist():
    fields = make_document_fields("payslip", {"employee_code": "UNKNOWN"})
    context = make_context(fields, reference_employees={"EMP001": "Salas Siguas, Katerin Karola"})
    result = await EmployeeCodeExistsInReferenceData().evaluate(context)
    assert not result.passed
    assert result.severity == "error"


@pytest.mark.asyncio
async def test_employee_name_fuzzy_lookup_matches(settings):
    fields = make_document_fields("payslip", {"employee_name": "Victor E. Espiritu Santiago"})
    context = make_context(fields, reference_employees={"EMP007": "Victor Emeric Espiritu Santiago"})
    rule = EmployeeNameExistsInReferenceData(settings)
    result = await rule.evaluate(context)
    assert result.passed
    assert result.confidence_method == "fuzzy_deterministic"


@pytest.mark.asyncio
async def test_employee_name_rule_does_not_apply_when_code_present(settings):
    fields = make_document_fields("payslip", {"employee_code": "EMP001", "employee_name": "Someone"})
    context = make_context(fields)
    rule = EmployeeNameExistsInReferenceData(settings)
    assert rule.applies_when(context) is False
