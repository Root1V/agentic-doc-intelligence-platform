"""Structured-output guarantee layer on top of ``llm/client.py``.

The endpoint behind ``reasoning_base_url``/``vision_base_url`` is served
externally and this project does not control what runs behind it, so it
cannot assume grammar/JSON-schema-constrained decoding (e.g. vLLM's
``guided_json``) is always available. Instructor's tool-calling-based
reask-on-``ValidationError`` loop is the path guaranteed to work against any
OpenAI-compatible server; constrained decoding is used opportunistically as
an optimization when ``settings.llm_supports_guided_json`` is True.
"""

from __future__ import annotations

from typing import TypeVar

import instructor
from pydantic import BaseModel

from idp.config import Settings
from idp.llm.client import Role, make_client

T = TypeVar("T", bound=BaseModel)


def instructor_client(settings: Settings, role: Role) -> instructor.Instructor:
    raw = make_client(settings, role)
    mode = instructor.Mode.JSON_SCHEMA if settings.llm_supports_guided_json else instructor.Mode.TOOLS
    return instructor.from_openai(raw, mode=mode)


def extract_structured(
    settings: Settings,
    *,
    role: Role,
    response_model: type[T],
    messages: list[dict],
    max_retries: int = 2,
) -> T:
    """One structured-output call, retried on schema-validation failure."""
    client = instructor_client(settings, role)
    model = settings.reasoning_model if role == "reasoning" else settings.vision_model
    return client.chat.completions.create(
        model=model,
        messages=messages,
        response_model=response_model,
        max_retries=max_retries,
    )
