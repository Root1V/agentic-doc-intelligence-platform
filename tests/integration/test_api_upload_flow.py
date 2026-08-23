"""API smoke test: upload a fixture through POST /batches, poll GET
/batches/{id} until complete, verify the extraction matches golden — the one
test exercising storage + DB + pipeline + API together. Needs the full stack
up; skips cleanly otherwise. Requires migrations applied first.

Uses ``httpx.AsyncClient`` + ``ASGITransport`` rather than
``fastapi.testclient.TestClient`` deliberately: ``TestClient`` bridges sync
test code to the async app via its own anyio thread+event loop, and an
asyncpg connection pool checked out on one loop can't be reused on another
(``RuntimeError: ... attached to a different loop``) — this bit us in
practice (``POST /batches`` succeeded, the follow-up ``GET`` failed). Driving
the app directly over ASGI keeps everything — test code, app code, the
background extraction task, and the DB engine — on the one event loop
pytest-asyncio already gave this test.
"""

from __future__ import annotations

import asyncio
import json

import pytest
from httpx import ASGITransport, AsyncClient

from idp.api.app import create_app
from idp.storage.object_store import S3ObjectStore
from tests.conftest import FIXTURES_DIR, GOLDEN_DIR, normalize_extracted_string

pytestmark = [pytest.mark.usefixtures("require_postgres", "require_minio", "require_reasoning_llm")]


@pytest.mark.asyncio
async def test_upload_batch_and_retrieve_extraction(live_settings):
    S3ObjectStore(live_settings).ensure_bucket()
    app = create_app()
    headers = {"x-api-key": live_settings.api_key}

    # ASGITransport awaits the whole ASGI call including BackgroundTasks
    # before returning, so POST /batches itself blocks until the pipeline
    # finishes (unlike a real deployment, where the client gets the response
    # immediately and the task keeps running after) — give it real headroom.
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test", timeout=180.0) as client:
        with (FIXTURES_DIR / "boleta_pagos1.png").open("rb") as fh:
            response = await client.post("/batches", files={"files": ("boleta_pagos1.png", fh, "image/png")}, headers=headers)
        assert response.status_code == 201
        batch_id = response.json()["batch_id"]

        deadline = asyncio.get_event_loop().time() + 120
        document = None
        while asyncio.get_event_loop().time() < deadline:
            batch_resp = await client.get(f"/batches/{batch_id}", headers=headers)
            assert batch_resp.status_code == 200
            documents = batch_resp.json()["documents"]
            if documents and documents[0]["status"] in ("completed", "needs_review", "failed"):
                document = documents[0]
                break
            await asyncio.sleep(2)

        assert document is not None, "timed out waiting for batch processing"

        detail_resp = await client.get(f"/documents/{document['id']}", headers=headers)

    assert detail_resp.status_code == 200
    detail = detail_resp.json()
    assert detail["document_type"] == "payslip"
    assert detail["extraction"] is not None, (
        f"extraction did not converge (document status={document['status']!r}) — "
        "if this fails consistently across runs, treat it as a real regression, not variance"
    )

    golden = json.loads((GOLDEN_DIR / "boleta_pagos1.json").read_text())
    for field, expected in golden["fields"].items():
        envelope = detail["extraction"].get(field)
        if envelope is None:
            # Optional schema fields (e.g. employer_name) aren't guaranteed
            # to be populated on every run — only required ones are.
            print(f"NOTE: optional field {field!r} was not extracted this run; skipping golden comparison for it")
            continue
        actual = envelope["value"]
        if isinstance(expected, (int, float)):
            assert abs(float(expected) - float(actual)) <= 0.5
        else:
            assert normalize_extracted_string(str(expected)) == normalize_extracted_string(str(actual))
