"""GET /audit — read-only correction history: every field a human ever
corrected via POST /review/{id}, who corrected it, and the before/after
value. `audit_log` has been populated since Phase 0 (a first-class
deliverable per its own model docstring), but nothing exposed it over HTTP
until now — this route only surfaces data that already existed."""

from __future__ import annotations

import uuid
from datetime import datetime

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from idp.api.deps import get_current_user, get_db_session
from idp.persistence.repositories import ReviewRepository

router = APIRouter(prefix="/audit", tags=["audit"], dependencies=[Depends(get_current_user)])


class AuditEntryResponse(BaseModel):
    id: uuid.UUID
    document_id: uuid.UUID
    field_path: str
    reviewer_identity: str
    original_value: dict
    corrected_value: dict
    original_confidence: float
    model_version: str | None
    prompt_version: str | None
    timestamp: datetime


class AuditLogResponse(BaseModel):
    total: int
    entries: list[AuditEntryResponse]


@router.get("", response_model=AuditLogResponse)
async def list_audit_log(
    limit: int = 50,
    offset: int = 0,
    session: AsyncSession = Depends(get_db_session),
) -> AuditLogResponse:
    repo = ReviewRepository(session)
    rows = await repo.list_audit_entries(limit=limit, offset=offset)
    total = await repo.count_audit_entries()
    return AuditLogResponse(
        total=total,
        entries=[
            AuditEntryResponse(
                id=row.id,
                document_id=row.review_item.document_id,
                field_path=row.review_item.field_path,
                reviewer_identity=row.reviewer_identity,
                original_value=row.original_value,
                corrected_value=row.corrected_value,
                original_confidence=row.original_confidence,
                model_version=row.model_version,
                prompt_version=row.prompt_version,
                timestamp=row.timestamp,
            )
            for row in rows
        ],
    )
