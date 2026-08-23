#!/usr/bin/env python
"""Runs every registered ``ParserBackend`` over the fixture corpus and
reports comparable per-backend metrics — latency, region counts, and a
lightweight text-coverage proxy against each fixture's golden field values.

This is the data the Fase 0 default parser choice (``PARSER_BACKEND``) is
meant to be based on, not a priori preference between Docling and PaddleOCR.
Run: ``uv run python scripts/compare_ocr_backends.py``
"""

from __future__ import annotations

import json
import time
import traceback
from pathlib import Path

from idp.config import get_settings
from idp.parsing.docling_backend import DoclingBackend
from idp.parsing.paddleocr_backend import PaddleOCRBackend

FIXTURES_DIR = Path(__file__).parent.parent / "tests" / "fixtures" / "documents"
GOLDEN_DIR = Path(__file__).parent.parent / "tests" / "golden" / "expected_extractions"


def _expected_strings(golden: dict) -> list[str]:
    fields = golden.get("fields", {})
    return [str(v) for v in fields.values() if isinstance(v, (str, int, float)) and str(v).strip()]


def run() -> list[dict]:
    settings = get_settings()
    backends = {"docling": DoclingBackend(settings), "paddleocr": PaddleOCRBackend(settings)}

    rows: list[dict] = []
    for image_path in sorted(FIXTURES_DIR.glob("*.png")):
        golden_path = GOLDEN_DIR / f"{image_path.stem}.json"
        golden = json.loads(golden_path.read_text()) if golden_path.exists() else {}
        expected = _expected_strings(golden)
        file_bytes = image_path.read_bytes()

        for backend_name, backend in backends.items():
            row: dict[str, object] = {"document": image_path.name, "backend": backend_name}
            start = time.monotonic()
            try:
                parsed = backend.parse(file_bytes, image_path.name)
                elapsed = time.monotonic() - start
                full_text = parsed.full_text.lower()
                hits = sum(1 for s in expected if s.lower() in full_text)
                coverage = round(hits / len(expected), 2) if expected else None
                row.update(
                    latency_s=round(elapsed, 2),
                    blocks=len(parsed.blocks),
                    table_regions=len(parsed.blocks_of_type("table")),
                    figure_regions=len(parsed.blocks_of_type("figure")),
                    expected_field_coverage=coverage,
                    error=None,
                )
            except Exception as exc:  # a backend failing on one doc shouldn't abort the comparison
                row.update(
                    latency_s=None,
                    blocks=None,
                    table_regions=None,
                    figure_regions=None,
                    expected_field_coverage=None,
                    error=f"{type(exc).__name__}: {exc}",
                )
                traceback.print_exc()
            rows.append(row)

    return rows


def print_table(rows: list[dict]) -> None:
    headers = ["document", "backend", "latency_s", "blocks", "table_regions", "figure_regions", "expected_field_coverage", "error"]
    widths = {h: max(len(h), *(len(str(r.get(h, ""))) for r in rows)) for h in headers} if rows else {h: len(h) for h in headers}
    print(" | ".join(h.ljust(widths[h]) for h in headers))
    print("-+-".join("-" * widths[h] for h in headers))
    for r in rows:
        print(" | ".join(str(r.get(h, "")).ljust(widths[h]) for h in headers))


if __name__ == "__main__":
    print_table(run())
