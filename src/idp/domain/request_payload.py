"""The optional external input a request/'solicitud' can arrive with.

A batch of one or more documents may be accompanied by data supplied via
JSON or a frontend form (e.g. an expected employee code, an expected total)
that request-input validation rules (category a) contrast against data
extracted from the documents in that same request.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class RequestInputPayload(BaseModel):
    """Value object: arbitrary externally-supplied fields for one request."""

    data: dict[str, Any] = Field(default_factory=dict)

    def get(self, key: str, default: Any = None) -> Any:
        return self.data.get(key, default)
