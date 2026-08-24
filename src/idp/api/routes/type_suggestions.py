"""GET /type-suggestions (pending queue) and POST /type-suggestions/{id}/accept
or /reject — a human decides whether a drafted ``DocumentType`` proposal
(see ``classification/type_discovery.py``) gets promoted. Accepting only
marks the proposal actionable; it does NOT register the type in
``domain/document_types.py`` — turning an accepted proposal into a real,
registered ``DocumentType`` (schema + extractor + prompts) remains a
deliberate code change, same as every type added to this platform so far."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from idp.api.deps import get_current_user, get_db_session
from idp.persistence.models import DocumentTypeSuggestion, User
from idp.persistence.repositories import TypeSuggestionRepository

router = APIRouter(prefix="/type-suggestions", tags=["type-suggestions"], dependencies=[Depends(get_current_user)])


class SuggestedFieldResponse(BaseModel):
    name: str
    field_type: str
    description: str
    required: bool


class TypeSuggestionResponse(BaseModel):
    id: uuid.UUID
    document_id: uuid.UUID
    batch_id: uuid.UUID
    suggested_type_name: str
    suggested_display_name: str
    rationale: str
    fields: list[dict]
    status: str
    reviewer_identity: str | None


def _to_response(row: DocumentTypeSuggestion) -> TypeSuggestionResponse:
    return TypeSuggestionResponse(
        id=row.id,
        document_id=row.document_id,
        batch_id=row.batch_id,
        suggested_type_name=row.suggested_type_name,
        suggested_display_name=row.suggested_display_name,
        rationale=row.rationale,
        fields=row.fields,
        status=row.status,
        reviewer_identity=row.reviewer_identity,
    )


@router.get("", response_model=list[TypeSuggestionResponse])
async def list_pending_suggestions(session: AsyncSession = Depends(get_db_session)) -> list[TypeSuggestionResponse]:
    repo = TypeSuggestionRepository(session)
    rows = await repo.list_pending()
    return [_to_response(row) for row in rows]


async def _resolve(suggestion_id: uuid.UUID, decision: str, reviewer_identity: str, session: AsyncSession) -> TypeSuggestionResponse:
    repo = TypeSuggestionRepository(session)
    row = await repo.get(suggestion_id)
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="type suggestion not found")
    row = await repo.resolve(suggestion_id, decision=decision, reviewer_identity=reviewer_identity)
    await session.commit()
    return _to_response(row)


@router.post("/{suggestion_id}/accept", response_model=TypeSuggestionResponse)
async def accept_suggestion(
    suggestion_id: uuid.UUID,
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
) -> TypeSuggestionResponse:
    return await _resolve(suggestion_id, "accepted", current_user.name, session)


@router.post("/{suggestion_id}/reject", response_model=TypeSuggestionResponse)
async def reject_suggestion(
    suggestion_id: uuid.UUID,
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
) -> TypeSuggestionResponse:
    return await _resolve(suggestion_id, "rejected", current_user.name, session)
