"""Phase 0 background-task entrypoint (FastAPI ``BackgroundTasks``). Owns its
own DB session — a background task outlives the HTTP request's DI scope, so
it cannot reuse a request-scoped session. This is the promotion seam for
Fase 1+: swapping this module's caller for a Prefect/Temporal worker doesn't
change ``pipeline.orchestrator.process_batch``'s signature."""

from __future__ import annotations

import uuid

from idp.config import Settings
from idp.persistence.db import get_session_factory
from idp.persistence.repositories import ReferenceDataRepository
from idp.pipeline.orchestrator import process_batch
from idp.storage.object_store import S3ObjectStore
from idp.validation.ports import StubExternalSystemPort


async def run_batch(settings: Settings, batch_id: uuid.UUID) -> None:
    factory = get_session_factory(settings)
    object_store = S3ObjectStore(settings)
    async with factory() as session:
        await process_batch(
            settings=settings,
            session=session,
            batch_id=batch_id,
            object_store=object_store,
            reference_data=ReferenceDataRepository(session),
            external_system=StubExternalSystemPort(),
        )
