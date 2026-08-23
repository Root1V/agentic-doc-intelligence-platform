"""GET /documents/{id} — extraction payload (with citations + reasoning_trace)
plus validation issues (with explanation), per the explainability design."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from idp.api.deps import get_db_session, require_api_key
from idp.persistence.repositories import DocumentRepository

router = APIRouter(prefix="/documents", tags=["documents"], dependencies=[Depends(require_api_key)])


class ValidationIssueResponse(BaseModel):
    rule_id: str
    category: str
    field_path: str | None
    severity: str
    message: str
    confidence: float
    confidence_method: str
    explanation: str


class DocumentDetailResponse(BaseModel):
    id: uuid.UUID
    status: str
    document_type: str | None
    classification_confidence: float | None
    needs_review: bool
    extraction: dict | None
    validation_issues: list[ValidationIssueResponse]


@router.get("/{document_id}", response_model=DocumentDetailResponse)
async def get_document(document_id: uuid.UUID, session: AsyncSession = Depends(get_db_session)) -> DocumentDetailResponse:
    repo = DocumentRepository(session)
    document = await repo.get(document_id)
    if document is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="document not found")

    return DocumentDetailResponse(
        id=document.id,
        status=document.status,
        document_type=document.document_type,
        classification_confidence=document.classification_confidence,
        needs_review=document.needs_review,
        extraction=document.extraction.payload if document.extraction else None,
        validation_issues=[
            ValidationIssueResponse(
                rule_id=issue.rule_id,
                category=issue.category,
                field_path=issue.field_path,
                severity=issue.severity,
                message=issue.message,
                confidence=issue.confidence,
                confidence_method=issue.confidence_method,
                explanation=issue.explanation,
            )
            for issue in document.validation_issues
        ],
    )
