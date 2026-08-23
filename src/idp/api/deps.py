"""Explicit dependency injection via FastAPI's ``Depends`` — deliberately not
module-level singletons (the PoC's ``ocr = PaddleOCR(...)`` anti-pattern)."""

from __future__ import annotations

from collections.abc import AsyncIterator
from typing import Annotated

from fastapi import Depends, Header, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from idp.config import Settings, get_settings
from idp.persistence.db import get_session_factory
from idp.persistence.repositories import ReferenceDataRepository
from idp.storage.object_store import S3ObjectStore
from idp.validation.ports import ExternalSystemPort, ReferenceDataPort, StubExternalSystemPort


def get_app_settings() -> Settings:
    return get_settings()


async def get_db_session(settings: Annotated[Settings, Depends(get_app_settings)]) -> AsyncIterator[AsyncSession]:
    factory = get_session_factory(settings)
    async with factory() as session:
        yield session


def get_object_store(settings: Annotated[Settings, Depends(get_app_settings)]) -> S3ObjectStore:
    return S3ObjectStore(settings)


def get_reference_data_port(session: Annotated[AsyncSession, Depends(get_db_session)]) -> ReferenceDataPort:
    return ReferenceDataRepository(session)


def get_external_system_port(settings: Annotated[Settings, Depends(get_app_settings)]) -> ExternalSystemPort:
    return StubExternalSystemPort()


async def require_api_key(
    settings: Annotated[Settings, Depends(get_app_settings)],
    x_api_key: Annotated[str | None, Header()] = None,
) -> None:
    if x_api_key != settings.api_key:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid API key")
