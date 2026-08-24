"""Extractor for ``DocumentType.DEBT_CAPACITY_CALCULATION``. Same bounded
agentic method as ``payslip.py``/``authorization_letter.py`` — see
``extraction/agentic/``."""

from __future__ import annotations

from idp.config import Settings
from idp.domain.document_types import DocumentType
from idp.domain.schemas.debt_capacity_calculation import DebtCapacityCalculationSchema
from idp.extraction.agentic.loop import ExtractionIncomplete, run_agentic_extraction
from idp.extraction.base import ExtractionOutcome, attach_trace
from idp.extraction.grounding import attach_grounding
from idp.extraction.registry import register_extractor
from idp.parsing.normalize import ParsedDocument


@register_extractor(DocumentType.DEBT_CAPACITY_CALCULATION)
class DebtCapacityCalculationExtractor:
    schema_version = "1.0"

    def extract(self, parsed: ParsedDocument, settings: Settings, correction_note: str | None = None) -> ExtractionOutcome:
        try:
            result, trace = run_agentic_extraction(
                settings, parsed, DebtCapacityCalculationSchema, DocumentType.DEBT_CAPACITY_CALCULATION, correction_note
            )
        except ExtractionIncomplete as exc:
            return ExtractionOutcome(schema_instance=None, needs_review=True, review_reason=str(exc), extraction_method="agentic")
        attach_trace(result, trace)
        attach_grounding(result, parsed)
        return ExtractionOutcome(schema_instance=result, needs_review=False, extraction_method="agentic")
