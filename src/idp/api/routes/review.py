"""GET /review (pending queue) and POST /review/{id} (submit a correction —
writes the full audit trail: original value/confidence, reviewer identity,
corrected value, timestamp, model/prompt version)."""

from __future__ import annotations

import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from idp.api.deps import get_db_session, require_api_key
from idp.persistence.repositories import ReviewRepository

router = APIRouter(prefix="/review", tags=["review"], dependencies=[Depends(require_api_key)])


class ReviewItemResponse(BaseModel):
    id: uuid.UUID
    document_id: uuid.UUID
    field_path: str
    current_value: dict
    confidence: float
    reason: str
    status: str


class ReviewCorrectionRequest(BaseModel):
    reviewer_identity: str
    corrected_value: Any
    model_version: str | None = None
    prompt_version: str | None = None


class ReviewCorrectionResponse(BaseModel):
    review_item_id: uuid.UUID
    status: str


@router.get("", response_model=list[ReviewItemResponse])
async def list_pending_review(session: AsyncSession = Depends(get_db_session)) -> list[ReviewItemResponse]:
    repo = ReviewRepository(session)
    items = await repo.list_pending()
    return [
        ReviewItemResponse(
            id=item.id,
            document_id=item.document_id,
            field_path=item.field_path,
            current_value=item.current_value,
            confidence=item.confidence,
            reason=item.reason,
            status=item.status,
        )
        for item in items
    ]


@router.post("/{review_item_id}", response_model=ReviewCorrectionResponse)
async def submit_correction(
    review_item_id: uuid.UUID,
    body: ReviewCorrectionRequest,
    session: AsyncSession = Depends(get_db_session),
) -> ReviewCorrectionResponse:
    repo = ReviewRepository(session)
    item = await repo.get(review_item_id)
    if item is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="review item not found")

    await repo.resolve(
        review_item_id,
        reviewer_identity=body.reviewer_identity,
        corrected_value={"value": body.corrected_value},
        model_version=body.model_version,
        prompt_version=body.prompt_version,
    )
    await session.commit()
    return ReviewCorrectionResponse(review_item_id=review_item_id, status="resolved")
