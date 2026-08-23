"""Integration tests need real infrastructure (Postgres/MinIO via
``docker compose up -d``, and a reachable LLM/VLM endpoint — e.g. the user's
own Prometheus serving project). These fixtures skip with a clear reason
instead of failing when that infra isn't available, since this project never
provisions it itself."""

from __future__ import annotations

import socket
from urllib.parse import urlparse

import pytest

from idp.config import Settings


def _port_open(host: str, port: int, timeout: float = 1.0) -> bool:
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except OSError:
        return False


@pytest.fixture(scope="session")
def live_settings() -> Settings:
    return Settings()


@pytest.fixture(scope="session")
def require_postgres(live_settings: Settings) -> None:
    url = urlparse(live_settings.database_url.replace("postgresql+asyncpg", "postgresql"))
    if not _port_open(url.hostname or "localhost", url.port or 5432):
        pytest.skip(f"Postgres no alcanzable en {url.hostname}:{url.port} (uv run docker compose up -d postgres)")


@pytest.fixture(scope="session")
def require_minio(live_settings: Settings) -> None:
    url = urlparse(live_settings.storage_endpoint_url)
    if not _port_open(url.hostname or "localhost", url.port or 9000):
        pytest.skip(f"MinIO no alcanzable en {url.hostname}:{url.port} (docker compose up -d minio)")


@pytest.fixture(scope="session")
def require_reasoning_llm(live_settings: Settings) -> None:
    url = urlparse(live_settings.reasoning_base_url)
    if not _port_open(url.hostname or "localhost", url.port or 80):
        pytest.skip(f"Endpoint LLM de razonamiento no alcanzable en {live_settings.reasoning_base_url} (configura Prometheus u otro servidor OpenAI-compatible)")
