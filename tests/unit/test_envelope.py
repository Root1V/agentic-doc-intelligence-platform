from __future__ import annotations

from idp.domain.envelope import Extracted, ToolCallRecord
from idp.domain.schemas.payslip import PayslipSchema
from idp.extraction.base import attach_trace


def _sample_payslip() -> PayslipSchema:
    return PayslipSchema(
        employee_name=Extracted(value="SALAS SIGUAS, KATERIN KAROLA", page=0, bbox=[0.1, 0.1, 0.5, 0.12], confidence=0.95, source_text="SALAS SIGUAS, KATERIN KAROLA"),
        period=Extracted(value="ENERO - 2026", page=0, bbox=None, confidence=0.9, source_text="PERIODO: ENERO - 2026"),
        gross_pay=Extracted(value=6618.00, page=0, bbox=None, confidence=0.98, source_text="6,618.00"),
        total_deductions=Extracted(value=2313.86, page=0, bbox=None, confidence=0.98, source_text="2,313.86"),
        net_pay=Extracted(value=4304.14, page=0, bbox=None, confidence=0.98, source_text="4,304.14"),
    )


def test_extracted_holds_grounding_fields():
    field = Extracted(value="hello", page=1, bbox=[0.0, 0.0, 1.0, 1.0], confidence=0.8, source_text="hello world")
    assert field.value == "hello"
    assert field.page == 1
    assert field.reasoning_trace is None


def test_attach_trace_is_noop_for_empty_trace():
    instance = _sample_payslip()
    attach_trace(instance, [])
    assert instance.employee_name.reasoning_trace is None


def test_attach_trace_stamps_every_leaf_including_nested():
    instance = _sample_payslip()
    trace = [ToolCallRecord(turn=1, tool_name="read_text_region", arguments={"region_id": 3}, result_summary="ok")]
    attach_trace(instance, trace)
    assert instance.employee_name.reasoning_trace == trace
    assert instance.net_pay.reasoning_trace == trace
