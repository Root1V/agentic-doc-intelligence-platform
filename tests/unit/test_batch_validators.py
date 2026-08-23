"""Category (b): cross-document validation, including the three fuzzy-match
sub-cases from the Fase 0 verification plan — clear match, clear no-match,
and an ambiguous case that escalates to a (mocked) LLM judge."""

from __future__ import annotations

import pytest

from idp.validation.entity_matching import EntityMatchVerdict
from idp.validation.rules import batch_rules
from idp.validation.rules.batch_rules import DuplicateDocumentIdentifier, EmployeeNameCrossDocumentMatch
from tests.conftest import make_context, make_document_fields


@pytest.mark.asyncio
async def test_duplicate_identifier_detected_within_batch():
    current = make_document_fields("payslip", {"employee_code": "EMP001"})
    sibling = make_document_fields("payslip", {"employee_code": "EMP001"})
    result = await DuplicateDocumentIdentifier().evaluate(make_context(current, siblings=[sibling]))
    assert not result.passed
    assert result.severity == "warning"


@pytest.mark.asyncio
async def test_no_duplicate_when_identifiers_differ():
    current = make_document_fields("payslip", {"employee_code": "EMP001"})
    sibling = make_document_fields("payslip", {"employee_code": "EMP002"})
    result = await DuplicateDocumentIdentifier().evaluate(make_context(current, siblings=[sibling]))
    assert result.passed


@pytest.mark.asyncio
async def test_employee_name_clear_match_is_fuzzy_deterministic(settings):
    # The exact case from the user's feedback: abbreviated middle name.
    # insured_* fields are split (first/paternal/maternal surname) — see
    # insurance_disclosure.py's schema comment for why — EmployeeNameCrossDocumentMatch
    # reassembles them into one name via batch_rules._full_name before comparing.
    current = make_document_fields("payslip", {"employee_name": "Victor Emeric Espiritu Santiago"})
    sibling = make_document_fields(
        "insurance_disclosure",
        {"insured_first_name": "Victor E.", "insured_paternal_surname": "Espiritu", "insured_maternal_surname": "Santiago"},
    )
    rule = EmployeeNameCrossDocumentMatch(settings)
    result = await rule.evaluate(make_context(current, siblings=[sibling]))
    assert result.passed
    assert result.confidence_method == "fuzzy_deterministic"
    assert result.confidence >= settings.entity_match_high_threshold


@pytest.mark.asyncio
async def test_employee_name_clear_no_match_is_fuzzy_deterministic(settings):
    current = make_document_fields("payslip", {"employee_name": "Ana Maria Rodriguez"})
    sibling = make_document_fields(
        "insurance_disclosure", {"insured_first_name": "Pedro", "insured_paternal_surname": "Gonzalez"}
    )
    rule = EmployeeNameCrossDocumentMatch(settings)
    result = await rule.evaluate(make_context(current, siblings=[sibling]))
    assert not result.passed
    assert result.confidence_method == "fuzzy_deterministic"
    assert result.severity == "warning"


@pytest.mark.asyncio
async def test_employee_name_ambiguous_case_escalates_to_llm_judge(settings, monkeypatch):
    current = make_document_fields("payslip", {"employee_name": "Rosa Delia Vega Castillo"})
    sibling = make_document_fields(
        "insurance_disclosure", {"insured_first_name": "R.", "insured_paternal_surname": "Vega", "insured_maternal_surname": "C."}
    )

    def fake_judge(_settings, *, kind, value_a, value_b, outcome):
        return EntityMatchVerdict(is_match=True, reasoning="Iniciales y apellidos coinciden; nombre compuesto abreviado.")

    monkeypatch.setattr(batch_rules, "escalate_to_llm_judge", fake_judge)

    rule = EmployeeNameCrossDocumentMatch(settings)
    result = await rule.evaluate(make_context(current, siblings=[sibling]))

    assert result.passed
    assert result.confidence_method == "llm_judge"
    assert "banda ambigua" in result.explanation
