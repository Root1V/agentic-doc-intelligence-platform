"""Batch orchestrator: runs every document in a batch through
parse -> classify -> extract -> persist, then a single unified validation
pass (all 6 rule categories, since cross-document/conditional rules need
every sibling's fields already extracted), then per-field review routing.

Deliberately NOT Temporal/Prefect in Phase 0 (see plan) — a plain async
function invoked from FastAPI ``BackgroundTasks``. Each stage is still
OTEL-traced and structured so promoting this to a durable workflow engine
later is mechanical, not a rewrite.
"""

from __future__ import annotations

import asyncio
import uuid
from typing import Any

from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from idp.classification.classifier import needs_review as classification_needs_review
from idp.config import Settings
from idp.domain.envelope import Extracted
from idp.domain.request_payload import RequestInputPayload
from idp.domain.schemas import schema_for
from idp.extraction.agentic.loop import ExtractionIncomplete
from idp.observability.otel import traced_stage
from idp.parsing.base import ParserBackend
from idp.parsing.docling_backend import DoclingBackend
from idp.parsing.paddleocr_backend import PaddleOCRBackend
from idp.persistence.models import ValidationIssue as ValidationIssueModel
from idp.persistence.repositories import (
    BatchRepository,
    DocumentRepository,
    ExtractionRepository,
    ReviewRepository,
    ValidationRepository,
)
from idp.parsing.normalize import ParsedDocument, slice_by_pages
from idp.pipeline.stages import classify_document, extract_document, parse_document, segment_document
from idp.review.queue import enqueue_review_items
from idp.review.routing import find_review_candidates
from idp.storage.object_store import ObjectStore
from idp.validation.base import ValidationRule
from idp.validation.context import DocumentFields, ValidationContext
from idp.validation.engine import run_validation
from idp.validation.ports import ExternalSystemPort, ReferenceDataPort
from idp.validation.rules.batch_rules import DuplicateDocumentIdentifier, EmployeeNameCrossDocumentMatch
from idp.validation.rules.external_system_rules import InsurancePolicyVerifiedExternally
from idp.validation.rules.reference_data_rules import EmployeeCodeExistsInReferenceData, EmployeeNameExistsInReferenceData
from idp.validation.rules.request_input_rules import ExpectedEmployeeCodeMatches
from idp.validation.rules.self_rules import DniFormatValid, PayslipArithmeticConsistency


def make_parser_backend(settings: Settings) -> ParserBackend:
    if settings.parser_backend == "docling":
        return DoclingBackend(settings)
    return PaddleOCRBackend(settings)


def build_default_rules(settings: Settings) -> list[ValidationRule]:
    """The registered rule set for Fase 0 — one or more concrete rules per
    of the 6 categories (5 from the user's feedback plus intra-document
    'self' checks)."""
    return [
        PayslipArithmeticConsistency(),
        DniFormatValid("insurance_disclosure", "insured_dni"),
        DniFormatValid("authorization_letter", "client_dni"),
        DniFormatValid("loan_application", "applicant_dni"),
        DniFormatValid("loan_approval_remittance", "applicant_dni"),
        DniFormatValid("loan_payment_schedule", "client_dni"),
        DniFormatValid("credit_summary", "member_dni"),
        DniFormatValid("account_statement", "member_dni"),
        DniFormatValid("debt_subrogation_authorization", "client_dni"),
        ExpectedEmployeeCodeMatches(),
        DuplicateDocumentIdentifier(),
        EmployeeNameCrossDocumentMatch(settings),
        EmployeeCodeExistsInReferenceData(),
        EmployeeNameExistsInReferenceData(settings),
        InsurancePolicyVerifiedExternally(),
    ]


def flatten_top_level_fields(instance: BaseModel) -> dict[str, Any]:
    """Unwraps top-level ``Extracted[T]`` leaves into plain field_path ->
    value for ``ValidationContext`` — rules never need to know about the
    citation envelope. Phase 0's rule set only references top-level fields;
    nested line items (e.g. ``concepts``) are not flattened."""
    out: dict[str, Any] = {}
    for name in type(instance).model_fields:
        value = getattr(instance, name)
        if isinstance(value, Extracted):
            out[name] = value.value
    return out


async def _classify_and_extract(
    *,
    settings: Settings,
    parsed: ParsedDocument,
    document_id: uuid.UUID,
    parser_backend_name: str,
    document_repo: DocumentRepository,
    extraction_repo: ExtractionRepository,
) -> DocumentFields | None:
    classification = await asyncio.to_thread(classify_document, settings, parsed, document_id=str(document_id))

    await document_repo.set_classification(
        document_id,
        document_type=classification.document_type.value,
        confidence=classification.confidence,
        reasoning=classification.reasoning,
        needs_review=classification_needs_review(settings, classification),
    )

    outcome = await asyncio.to_thread(
        extract_document, settings, parsed, classification.document_type, document_id=str(document_id)
    )

    if outcome.schema_instance is None:
        await document_repo.mark_needs_review(document_id)
        await document_repo.set_status(document_id, "needs_review")
        return None

    await extraction_repo.save(
        document_id=document_id,
        schema_version="1.0",
        payload=outcome.schema_instance.model_dump(mode="json"),
        parser_backend=parser_backend_name,
        extraction_method=outcome.extraction_method,
    )
    await document_repo.set_status(document_id, "extracted")

    return DocumentFields(
        document_id=document_id,
        document_type=classification.document_type.value,
        fields=flatten_top_level_fields(outcome.schema_instance),
    )


async def _process_uploaded_file(
    *,
    settings: Settings,
    backend: ParserBackend,
    batch_id: uuid.UUID,
    document_id: uuid.UUID,
    storage_key: str,
    filename: str,
    object_store: ObjectStore,
    document_repo: DocumentRepository,
    extraction_repo: ExtractionRepository,
) -> list[DocumentFields]:
    """Parses the raw physical upload once, then checks whether it actually
    bundles more than one logical document (segmentation.detect_segments —
    see that module's docstring for why this exists: a real 7-page PDF
    turned out to be an email + a payment schedule + contract T&Cs + an
    account statement, and forcing all of it through one classify->extract
    pass timed out repeatedly).

    The common case (one segment covering the whole file) processes in
    place using the ``document_id`` row already created at upload time — no
    new rows, no behavior change for anything that worked before
    segmentation existed. Extra segments each get their own child Document
    row (same storage_key — it's the same physical file, no re-upload) and
    are classified/extracted independently, with per-segment failure
    isolation matching the existing per-document isolation in
    ``process_batch``."""
    file_bytes = await asyncio.to_thread(object_store.get, storage_key)
    parsed = await asyncio.to_thread(parse_document, settings, backend, file_bytes, filename, document_id=str(document_id))
    segments = await asyncio.to_thread(segment_document, settings, parsed, document_id=str(document_id))

    if len(segments) <= 1:
        fields = await _classify_and_extract(
            settings=settings,
            parsed=parsed,
            document_id=document_id,
            parser_backend_name=backend.name,
            document_repo=document_repo,
            extraction_repo=extraction_repo,
        )
        return [fields] if fields is not None else []

    await document_repo.set_status(document_id, "segmented")
    all_fields: list[DocumentFields] = []
    for segment in segments:
        sliced = slice_by_pages(parsed, segment.start_page, segment.end_page)
        child = await document_repo.create_child(
            batch_id=batch_id,
            parent_document_id=document_id,
            storage_key=storage_key,
            original_filename=f"{filename}#p{segment.start_page}-{segment.end_page}",
            page_start=segment.start_page,
            page_end=segment.end_page,
        )
        try:
            fields = await _classify_and_extract(
                settings=settings,
                parsed=sliced,
                document_id=child.id,
                parser_backend_name=backend.name,
                document_repo=document_repo,
                extraction_repo=extraction_repo,
            )
        except ExtractionIncomplete:
            await document_repo.mark_needs_review(child.id)
            await document_repo.set_status(child.id, "needs_review")
            fields = None
        except Exception:
            await document_repo.set_status(child.id, "failed")
            fields = None
        if fields is not None:
            all_fields.append(fields)
    return all_fields


async def process_batch(
    *,
    settings: Settings,
    session: AsyncSession,
    batch_id: uuid.UUID,
    object_store: ObjectStore,
    reference_data: ReferenceDataPort,
    external_system: ExternalSystemPort,
) -> None:
    batch_repo = BatchRepository(session)
    document_repo = DocumentRepository(session)
    extraction_repo = ExtractionRepository(session)
    validation_repo = ValidationRepository(session)
    review_repo = ReviewRepository(session)

    batch = await batch_repo.get(batch_id)
    if batch is None:
        raise ValueError(f"batch not found: {batch_id}")

    await batch_repo.set_status(batch_id, "processing")
    await session.commit()
    backend = make_parser_backend(settings)
    request_payload = RequestInputPayload(data=batch.request_input_payload or {})

    all_fields: list[DocumentFields] = []
    for document in batch.documents:
        with traced_stage("process_document", batch_id=str(batch_id), document_id=str(document.id)):
            try:
                fields = await _process_uploaded_file(
                    settings=settings,
                    backend=backend,
                    batch_id=batch_id,
                    document_id=document.id,
                    storage_key=document.storage_key,
                    filename=document.original_filename,
                    object_store=object_store,
                    document_repo=document_repo,
                    extraction_repo=extraction_repo,
                )
            except ExtractionIncomplete:
                await document_repo.mark_needs_review(document.id)
                await document_repo.set_status(document.id, "needs_review")
                fields = []
            except Exception:
                # A single document's failure (e.g. the configured LLM/VLM
                # endpoint being unreachable) must not leave the whole batch
                # stuck in "processing" with nothing committed — mark this
                # document failed and keep going with the rest of the batch.
                # The OTEL span above already records the exception.
                await document_repo.set_status(document.id, "failed")
                fields = []
        await session.commit()
        all_fields.extend(fields)

    rules = build_default_rules(settings)
    for current in all_fields:
        siblings = [f for f in all_fields if f.document_id != current.document_id]
        context = ValidationContext(
            batch_id=batch_id,
            current_document=current,
            sibling_documents=siblings,
            request_payload=request_payload,
            reference_data=reference_data,
            external_system=external_system,
        )
        try:
            with traced_stage("validate", batch_id=str(batch_id), document_id=str(current.document_id)):
                results = await run_validation(rules, context)

            for result in results:
                if not result.passed:
                    await validation_repo.save_issue(
                        ValidationIssueModel(
                            document_id=current.document_id,
                            batch_id=batch_id,
                            rule_id=result.rule_id,
                            category=result.category.value,
                            field_path=result.field_path,
                            severity=result.severity.value if result.severity else "warning",
                            message=result.message,
                            expected=_jsonable(result.expected),
                            actual=_jsonable(result.actual),
                            confidence=result.confidence,
                            confidence_method=result.confidence_method.value,
                            explanation=result.explanation,
                        )
                    )

            document = await document_repo.get(current.document_id)
            if document is not None and document.extraction is not None:
                schema_cls = schema_for(current.document_type)
                schema_instance = schema_cls.model_validate(document.extraction.payload)
                candidates = find_review_candidates(schema_instance, results, confidence_threshold=settings.review_confidence_threshold)
                if candidates:
                    await enqueue_review_items(review_repo, document_id=current.document_id, candidates=candidates)
                    await document_repo.mark_needs_review(current.document_id)
                await document_repo.set_status(current.document_id, "needs_review" if candidates else "completed")
        except Exception:
            # Same principle as the extraction loop: one document's
            # validation blowing up (e.g. a reference-data/external-system
            # port erroring) must not lose the rest of the batch's progress.
            await document_repo.set_status(current.document_id, "failed")
        await session.commit()

    await batch_repo.set_status(batch_id, "completed")
    await session.commit()


def _jsonable(value: Any) -> Any:
    if value is None or isinstance(value, (str, int, float, bool)):
        return {"value": value} if not isinstance(value, dict) else value
    return {"value": str(value)}
