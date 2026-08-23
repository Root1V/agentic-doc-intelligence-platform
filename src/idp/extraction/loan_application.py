"""Extractor for ``DocumentType.LOAN_APPLICATION``. Same bounded agentic
method as the other schema-driven extractors — see ``extraction/agentic/``.
This form is multi-page and dense (personal/employment/spouse/patrimony
sections), which is exactly the case the bounded loop is meant for: the
agent inspects only the sections it needs for the fixed target schema."""

from __future__ import annotations

from idp.config import Settings
from idp.domain.document_types import DocumentType
from idp.domain.schemas.loan_application import LoanApplicationSchema
from idp.extraction.agentic.loop import ExtractionIncomplete, run_agentic_extraction
from idp.extraction.base import ExtractionOutcome, attach_trace
from idp.extraction.grounding import attach_grounding
from idp.extraction.registry import register_extractor
from idp.parsing.normalize import ParsedDocument


@register_extractor(DocumentType.LOAN_APPLICATION)
class LoanApplicationExtractor:
    schema_version = "1.0"

    def extract(self, parsed: ParsedDocument, settings: Settings, correction_note: str | None = None) -> ExtractionOutcome:
        try:
            result, trace = run_agentic_extraction(
                settings, parsed, LoanApplicationSchema, DocumentType.LOAN_APPLICATION, correction_note
            )
        except ExtractionIncomplete as exc:
            return ExtractionOutcome(schema_instance=None, needs_review=True, review_reason=str(exc), extraction_method="agentic")
        attach_trace(result, trace)
        attach_grounding(result, parsed)
        return ExtractionOutcome(schema_instance=result, needs_review=False, extraction_method="agentic")
