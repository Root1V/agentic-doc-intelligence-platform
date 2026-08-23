"""Repository pattern: the only layer allowed to build SQLAlchemy queries.
Domain/service code depends on these, never on ``models.py`` + raw queries
directly."""

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from idp.persistence.models import (
    AuditLogEntry,
    Batch,
    Document,
    Extraction,
    ReferenceEmployee,
    ReviewItem,
    ValidationIssue,
)


class BatchRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, *, tenant: str = "default", request_input_payload: dict | None = None) -> Batch:
        batch = Batch(tenant=tenant, request_input_payload=request_input_payload)
        self._session.add(batch)
        await self._session.flush()
        return batch

    async def get(self, batch_id: uuid.UUID) -> Batch | None:
        # populate_existing=True — see DocumentRepository.get() for why this
        # is required, not optional: without it, polling GET /batches/{id}
        # within the same session as an in-flight pipeline run can return
        # stale (pre-extraction) document/relationship state.
        stmt = (
            select(Batch)
            .where(Batch.id == batch_id)
            .options(
                selectinload(Batch.documents).selectinload(Document.extraction),
                selectinload(Batch.documents).selectinload(Document.validation_issues),
            )
            .execution_options(populate_existing=True)
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def set_status(self, batch_id: uuid.UUID, status: str) -> None:
        batch = await self._session.get(Batch, batch_id)
        if batch is not None:
            batch.status = status


class DocumentRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, *, batch_id: uuid.UUID, storage_key: str, original_filename: str) -> Document:
        doc = Document(batch_id=batch_id, storage_key=storage_key, original_filename=original_filename)
        self._session.add(doc)
        await self._session.flush()
        return doc

    async def get(self, document_id: uuid.UUID) -> Document | None:
        # populate_existing=True: without it, SQLAlchemy's identity map can
        # return an already-loaded Document from earlier in the same session
        # with a stale (e.g. still-None) `.extraction` relationship, even
        # though an Extraction row was inserted afterward — because that
        # insert never touched this Document instance's Python-side
        # relationship attribute, only the FK on the new row.
        stmt = (
            select(Document)
            .where(Document.id == document_id)
            .options(
                selectinload(Document.extraction),
                selectinload(Document.validation_issues),
                selectinload(Document.review_items),
            )
            .execution_options(populate_existing=True)
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_for_batch(self, batch_id: uuid.UUID) -> list[Document]:
        stmt = select(Document).where(Document.batch_id == batch_id).options(selectinload(Document.extraction))
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def set_classification(self, document_id: uuid.UUID, *, document_type: str, confidence: float, reasoning: str, needs_review: bool) -> None:
        doc = await self._session.get(Document, document_id)
        if doc is not None:
            doc.document_type = document_type
            doc.classification_confidence = confidence
            doc.classification_reasoning = reasoning
            doc.needs_review = doc.needs_review or needs_review

    async def set_status(self, document_id: uuid.UUID, status: str) -> None:
        doc = await self._session.get(Document, document_id)
        if doc is not None:
            doc.status = status

    async def mark_needs_review(self, document_id: uuid.UUID) -> None:
        doc = await self._session.get(Document, document_id)
        if doc is not None:
            doc.needs_review = True


class ExtractionRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def save(self, *, document_id: uuid.UUID, schema_version: str, payload: dict, parser_backend: str, extraction_method: str) -> Extraction:
        extraction = Extraction(
            document_id=document_id,
            schema_version=schema_version,
            payload=payload,
            parser_backend=parser_backend,
            extraction_method=extraction_method,
        )
        self._session.add(extraction)
        await self._session.flush()
        return extraction


class ValidationRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def save_issue(self, issue: ValidationIssue) -> ValidationIssue:
        self._session.add(issue)
        await self._session.flush()
        return issue

    async def list_for_batch(self, batch_id: uuid.UUID) -> list[ValidationIssue]:
        stmt = select(ValidationIssue).where(ValidationIssue.batch_id == batch_id)
        result = await self._session.execute(stmt)
        return list(result.scalars().all())


class ReviewRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create_item(self, item: ReviewItem) -> ReviewItem:
        self._session.add(item)
        await self._session.flush()
        return item

    async def list_pending(self) -> list[ReviewItem]:
        stmt = select(ReviewItem).where(ReviewItem.status == "pending")
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def get(self, review_item_id: uuid.UUID) -> ReviewItem | None:
        return await self._session.get(ReviewItem, review_item_id)

    async def resolve(self, review_item_id: uuid.UUID, *, reviewer_identity: str, corrected_value: dict, model_version: str | None = None, prompt_version: str | None = None) -> AuditLogEntry:
        item = await self._session.get(ReviewItem, review_item_id)
        if item is None:
            raise ValueError(f"review item not found: {review_item_id}")
        entry = AuditLogEntry(
            review_item_id=item.id,
            original_value=item.current_value,
            original_confidence=item.confidence,
            reviewer_identity=reviewer_identity,
            corrected_value=corrected_value,
            model_version=model_version,
            prompt_version=prompt_version,
        )
        item.status = "resolved"
        self._session.add(entry)
        await self._session.flush()
        return entry


class ReferenceDataRepository:
    """Postgres-backed adapter of ``ReferenceDataPort`` (category d)."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def find_employee_by_code(self, employee_code: str) -> dict | None:
        stmt = select(ReferenceEmployee).where(ReferenceEmployee.employee_code == employee_code)
        result = await self._session.execute(stmt)
        employee = result.scalar_one_or_none()
        if employee is None:
            return None
        return {"employee_code": employee.employee_code, "full_name": employee.full_name, "active": employee.active}

    async def list_active_employee_names(self) -> list[tuple[str, str]]:
        stmt = select(ReferenceEmployee).where(ReferenceEmployee.active.is_(True))
        result = await self._session.execute(stmt)
        return [(e.employee_code, e.full_name) for e in result.scalars().all()]
