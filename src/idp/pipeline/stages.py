"""Thin, synchronous stage functions — the seam designed for a mechanical
promotion to Prefect/Temporal in Fase 1+: each stage is ``(input, context)
-> output``, OTEL-traced, with no knowledge of persistence or orchestration.
Kept synchronous (LLM/OCR calls are blocking) and run via
``asyncio.to_thread`` from the async orchestrator."""

from __future__ import annotations

from idp.classification.classifier import ClassificationResult, classify
from idp.config import Settings
from idp.domain.document_types import DocumentType
from idp.extraction.base import ExtractionOutcome
from idp.extraction.registry import get_extractor
from idp.observability.otel import traced_stage
from idp.parsing.base import ParserBackend
from idp.parsing.normalize import ParsedDocument


def parse_document(settings: Settings, backend: ParserBackend, file_bytes: bytes, filename: str, *, document_id: str) -> ParsedDocument:
    with traced_stage("parse", document_id=document_id, backend=backend.name):
        return backend.parse(file_bytes, filename)


def classify_document(settings: Settings, parsed: ParsedDocument, *, document_id: str) -> ClassificationResult:
    with traced_stage("classify", document_id=document_id):
        return classify(settings, parsed)


def extract_document(
    settings: Settings,
    parsed: ParsedDocument,
    document_type: DocumentType,
    *,
    document_id: str,
    correction_note: str | None = None,
) -> ExtractionOutcome:
    with traced_stage("extract", document_id=document_id, document_type=document_type.value):
        extractor = get_extractor(document_type)
        return extractor.extract(parsed, settings, correction_note)
