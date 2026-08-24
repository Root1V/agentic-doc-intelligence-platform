"""GET /document-types — read-only catalog of every known DocumentType: its
description and its schema's field list, introspected directly from the
Pydantic schema classes (``SCHEMA_BY_DOCUMENT_TYPE``) so the catalog can
never drift from what the extractors actually produce. Also surfaces
accepted-but-not-yet-coded type suggestions as 'plantillas en revision de
ingenieria' — see the plan's 'Plantillas -> catalogo de tipos de documento'
decision. Nothing here is editable: registering a type is still a
deliberate code change (new schema + extractor + prompts), same as every
type added to this platform so far."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from idp.api.deps import get_current_user, get_db_session
from idp.classification.classifier import TYPE_DESCRIPTIONS
from idp.domain.document_types import DocumentType
from idp.domain.schemas import SCHEMA_BY_DOCUMENT_TYPE
from idp.persistence.repositories import TypeSuggestionRepository

router = APIRouter(prefix="/document-types", tags=["document-types"], dependencies=[Depends(get_current_user)])


class FieldInfo(BaseModel):
    name: str
    field_type: str
    description: str | None
    required: bool


class DocumentTypeInfo(BaseModel):
    name: str
    description: str
    fields: list[FieldInfo]


class PendingTypeInfo(BaseModel):
    suggestion_id: str
    suggested_type_name: str
    suggested_display_name: str
    rationale: str
    fields: list[dict]


class DocumentTypeCatalogResponse(BaseModel):
    registered: list[DocumentTypeInfo]
    pending: list[PendingTypeInfo]


def _clean_type(annotation: object) -> str:
    text = str(annotation)
    return text.replace("idp.domain.envelope.Extracted", "Extracted").replace("<class '", "").replace("'>", "")


@router.get("", response_model=DocumentTypeCatalogResponse)
async def get_document_type_catalog(session: AsyncSession = Depends(get_db_session)) -> DocumentTypeCatalogResponse:
    registered = []
    for doc_type, schema_cls in SCHEMA_BY_DOCUMENT_TYPE.items():
        if doc_type == DocumentType.GENERIC:
            continue
        fields = [
            FieldInfo(
                name=field_name,
                field_type=_clean_type(field_info.annotation),
                description=field_info.description,
                required=field_info.is_required(),
            )
            for field_name, field_info in schema_cls.model_fields.items()
        ]
        registered.append(DocumentTypeInfo(name=doc_type.value, description=TYPE_DESCRIPTIONS.get(doc_type, ""), fields=fields))

    accepted_suggestions = await TypeSuggestionRepository(session).list_by_status("accepted")
    pending = [
        PendingTypeInfo(
            suggestion_id=str(row.id),
            suggested_type_name=row.suggested_type_name,
            suggested_display_name=row.suggested_display_name,
            rationale=row.rationale,
            fields=row.fields,
        )
        for row in accepted_suggestions
    ]

    return DocumentTypeCatalogResponse(registered=registered, pending=pending)
