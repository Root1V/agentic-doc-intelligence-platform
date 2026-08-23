"""Extractor for ``DocumentType.AUTHORIZATION_LETTER``. Same bounded agentic
method as ``payslip.py``/``insurance_disclosure.py`` — see
``extraction/agentic/``. Different institutions (banks, employers) issue
these with different layouts, so the schema stays fixed while the method
inspects regions dynamically."""

from __future__ import annotations

from idp.config import Settings
from idp.domain.document_types import DocumentType
from idp.domain.schemas.authorization_letter import AuthorizationLetterSchema
from idp.extraction.agentic.loop import ExtractionIncomplete, run_agentic_extraction
from idp.extraction.base import ExtractionOutcome, attach_trace
from idp.extraction.grounding import attach_grounding
from idp.extraction.registry import register_extractor
from idp.parsing.normalize import ParsedDocument


@register_extractor(DocumentType.AUTHORIZATION_LETTER)
class AuthorizationLetterExtractor:
    schema_version = "1.0"

    def extract(self, parsed: ParsedDocument, settings: Settings, correction_note: str | None = None) -> ExtractionOutcome:
        try:
            result, trace = run_agentic_extraction(
                settings, parsed, AuthorizationLetterSchema, DocumentType.AUTHORIZATION_LETTER, correction_note
            )
        except ExtractionIncomplete as exc:
            return ExtractionOutcome(schema_instance=None, needs_review=True, review_reason=str(exc), extraction_method="agentic")
        attach_trace(result, trace)
        attach_grounding(result, parsed)
        return ExtractionOutcome(schema_instance=result, needs_review=False, extraction_method="agentic")
