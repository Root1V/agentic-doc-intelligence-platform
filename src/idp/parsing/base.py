"""Port: the parser-backend abstraction. Adapters (``docling_backend.py``,
``paddleocr_backend.py``) implement this so the rest of the pipeline never
depends on a concrete OCR/layout engine."""

from __future__ import annotations

from typing import Protocol

from idp.parsing.normalize import ParsedDocument


class ParserBackend(Protocol):
    name: str

    def parse(self, file_bytes: bytes, filename: str) -> ParsedDocument: ...
