"""Thin service layer turning ``ReviewCandidate``s into persisted
``ReviewItem`` rows via the repository — the API layer's review endpoints
read/write through the same repository."""

from __future__ import annotations

import uuid

from idp.persistence.models import ReviewItem
from idp.persistence.repositories import ReviewRepository
from idp.review.routing import ReviewCandidate


async def enqueue_review_items(
    repo: ReviewRepository, *, document_id: uuid.UUID, candidates: list[ReviewCandidate]
) -> list[ReviewItem]:
    items: list[ReviewItem] = []
    for candidate in candidates:
        item = ReviewItem(
            document_id=document_id,
            field_path=candidate.field_path,
            current_value={"value": candidate.value},
            confidence=candidate.confidence,
            reason=candidate.reason,
        )
        items.append(await repo.create_item(item))
    return items
