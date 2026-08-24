"""POST /batches (upload) and GET /batches/{id} (status + documents)."""

from __future__ import annotations

import json
import uuid
from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, Depends, File, Form, HTTPException, UploadFile, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from idp.api.deps import get_app_settings, get_current_user, get_db_session, get_object_store
from idp.api.schemas import DocumentSummary
from idp.config import Settings
from idp.persistence.repositories import BatchRepository, DocumentRepository
from idp.storage.object_store import S3ObjectStore
from idp.worker.tasks import run_batch

router = APIRouter(prefix="/batches", tags=["batches"], dependencies=[Depends(get_current_user)])


class BatchStatusResponse(BaseModel):
    id: uuid.UUID
    status: str
    documents: list[DocumentSummary]


class BatchCreateResponse(BaseModel):
    batch_id: uuid.UUID


@router.post("", response_model=BatchCreateResponse, status_code=status.HTTP_201_CREATED)
async def create_batch(
    background_tasks: BackgroundTasks,
    files: Annotated[list[UploadFile], File(...)],
    request_input_payload: Annotated[str | None, Form()] = None,
    session: AsyncSession = Depends(get_db_session),
    settings: Settings = Depends(get_app_settings),
    object_store: S3ObjectStore = Depends(get_object_store),
) -> BatchCreateResponse:
    payload_dict = json.loads(request_input_payload) if request_input_payload else None

    batch_repo = BatchRepository(session)
    document_repo = DocumentRepository(session)

    batch = await batch_repo.create(request_input_payload=payload_dict)

    for upload in files:
        content = await upload.read()
        document = await document_repo.create(batch_id=batch.id, storage_key="", original_filename=upload.filename or "unnamed")
        storage_key = object_store.key_for(tenant="default", batch_id=str(batch.id), document_id=str(document.id), filename=upload.filename or "original")
        document.storage_key = storage_key
        object_store.put(storage_key, content, content_type=upload.content_type or "application/octet-stream")

    await session.commit()

    background_tasks.add_task(run_batch, settings, batch.id)

    return BatchCreateResponse(batch_id=batch.id)


@router.get("/{batch_id}", response_model=BatchStatusResponse)
async def get_batch(batch_id: uuid.UUID, session: AsyncSession = Depends(get_db_session)) -> BatchStatusResponse:
    batch_repo = BatchRepository(session)
    batch = await batch_repo.get(batch_id)
    if batch is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="batch not found")
    return BatchStatusResponse(
        id=batch.id,
        status=batch.status,
        documents=[
            DocumentSummary(
                id=doc.id,
                batch_id=doc.batch_id,
                status=doc.status,
                document_type=doc.document_type,
                classification_confidence=doc.classification_confidence,
                needs_review=doc.needs_review,
                original_filename=doc.original_filename,
                parent_document_id=doc.parent_document_id,
                page_start=doc.page_start,
                page_end=doc.page_end,
            )
            for doc in batch.documents
        ],
    )
