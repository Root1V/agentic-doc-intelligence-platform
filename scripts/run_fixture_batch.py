#!/usr/bin/env python
"""Runs the full fixture corpus through the live API (one document per batch)
and diffs the extracted values against the golden files — the command to run
after any pipeline change to confirm Fase 0 still works end-to-end.

Requires the API running (``uvicorn idp.api.app:app``) with Postgres/MinIO up
(``docker compose up -d``) and a reachable LLM/VLM endpoint (e.g. Prometheus).
Run: ``uv run python scripts/run_fixture_batch.py [--base-url http://localhost:8000]``
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import httpx

FIXTURES_DIR = Path(__file__).parent.parent / "tests" / "fixtures" / "documents"
GOLDEN_DIR = Path(__file__).parent.parent / "tests" / "golden" / "expected_extractions"
TERMINAL_STATUSES = {"completed", "needs_review", "failed"}
NUMERIC_TOLERANCE = 0.01


def _values_match(expected, actual) -> bool:
    if isinstance(expected, (int, float)) and isinstance(actual, (int, float)):
        return abs(float(expected) - float(actual)) <= NUMERIC_TOLERANCE
    return str(expected).strip().lower() == str(actual).strip().lower()


def _diff_fields(expected_fields: dict, extraction_payload: dict) -> list[tuple[str, bool, object, object]]:
    rows = []
    for field, expected_value in expected_fields.items():
        envelope = extraction_payload.get(field)
        actual_value = envelope.get("value") if isinstance(envelope, dict) else None
        rows.append((field, _values_match(expected_value, actual_value), expected_value, actual_value))
    return rows


def run(base_url: str, api_key: str, timeout_s: float = 300.0) -> int:
    client = httpx.Client(base_url=base_url, headers={"x-api-key": api_key}, timeout=30.0)
    exit_code = 0

    for image_path in sorted(FIXTURES_DIR.glob("*.png")):
        golden_path = GOLDEN_DIR / f"{image_path.stem}.json"
        golden = json.loads(golden_path.read_text()) if golden_path.exists() else {}
        expected_fields = golden.get("fields", {})

        print(f"\n=== {image_path.name} ===")
        with image_path.open("rb") as fh:
            resp = client.post("/batches", files={"files": (image_path.name, fh, "image/png")})
        resp.raise_for_status()
        batch_id = resp.json()["batch_id"]

        deadline = time.monotonic() + timeout_s
        status = None
        document = None
        while time.monotonic() < deadline:
            batch_resp = client.get(f"/batches/{batch_id}")
            batch_resp.raise_for_status()
            body = batch_resp.json()
            documents = body.get("documents", [])
            if documents:
                document = documents[0]
                status = document["status"]
                if status in TERMINAL_STATUSES:
                    break
            time.sleep(2)

        if document is None or status not in TERMINAL_STATUSES:
            print(f"  TIMEOUT esperando resultado (ultimo status={status})")
            exit_code = 1
            continue

        detail_resp = client.get(f"/documents/{document['id']}")
        detail_resp.raise_for_status()
        detail = detail_resp.json()
        extraction_payload = detail.get("extraction") or {}

        print(f"  document_type={detail['document_type']} classification_confidence={detail['classification_confidence']}")
        rows = _diff_fields(expected_fields, extraction_payload)
        for field, ok, expected_value, actual_value in rows:
            mark = "PASS" if ok else "FAIL"
            print(f"  [{mark}] {field}: esperado={expected_value!r} obtenido={actual_value!r}")
            if not ok:
                exit_code = 1

        if detail["validation_issues"]:
            print("  Validation issues:")
            for issue in detail["validation_issues"]:
                print(f"    - [{issue['severity']}] {issue['rule_id']}: {issue['message']}")

    return exit_code


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", default="http://localhost:8000")
    parser.add_argument("--api-key", default="dev-local-api-key")
    args = parser.parse_args()
    sys.exit(run(args.base_url, args.api_key))
