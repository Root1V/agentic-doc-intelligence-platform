"""Port: the extractor abstraction. Whether a concrete extractor uses the
bounded agentic loop (payslip, insurance_disclosure) or a single fixed call
(generic) is a strategy decision made per document type in ``registry.py`` —
the orchestrator never knows which."""

from __future__ import annotations

from typing import Protocol

from pydantic import BaseModel

from idp.config import Settings
from idp.domain.envelope import Extracted, ToolCallRecord
from idp.parsing.normalize import ParsedDocument


class ExtractionOutcome(BaseModel):
    """Wraps an extractor's result plus whether it needs human review because
    the bounded loop could not converge (turns exhausted without valid
    output) — extraction succeeding structurally is not the same as
    extraction succeeding *confidently*."""

    model_config = {"arbitrary_types_allowed": True}

    schema_instance: BaseModel | None
    needs_review: bool
    review_reason: str | None = None
    extraction_method: str = "fixed"  # "agentic" | "fixed"


class BaseExtractor(Protocol):
    schema_version: str

    def extract(
        self, parsed: ParsedDocument, settings: Settings, correction_note: str | None = None
    ) -> ExtractionOutcome: ...


def attach_trace(instance: BaseModel, trace: list[ToolCallRecord]) -> None:
    """Recursively stamps every ``Extracted[T]`` leaf in a schema instance
    with the agentic loop's tool-call trace, so "why did the agent look
    here" is reconstructable from any field, not just the ones a tool call
    happened to target directly."""
    if not trace:
        return
    _attach_recursive(instance, trace)


def _attach_recursive(value: object, trace: list[ToolCallRecord]) -> None:
    if isinstance(value, Extracted):
        value.reasoning_trace = trace
    elif isinstance(value, BaseModel):
        for field_name in type(value).model_fields:
            _attach_recursive(getattr(value, field_name), trace)
    elif isinstance(value, list):
        for item in value:
            _attach_recursive(item, trace)
