"""Thin, configurable wrapper over OpenAI-compatible chat endpoints.

This module never starts, hosts, or manages a model-serving process. It
assumes something OpenAI-compatible is already listening at the configured
``base_url`` for each role (e.g. the user's own Prometheus serving project,
or anything else speaking the same protocol) and simply points at it.

Two roles are modeled, matching the PoC's two-tier LLM usage:
  - "reasoning": text LLM driving classification and the agentic extraction
    loop's turn-taking.
  - "vision": VLM invoked by extraction tools that need to read a cropped
    region image (tables/figures).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from openai import OpenAI

from idp.config import Settings

Role = Literal["reasoning", "vision"]


@dataclass(frozen=True)
class RoleConfig:
    base_url: str
    model: str
    api_key: str


def role_config(settings: Settings, role: Role) -> RoleConfig:
    if role == "reasoning":
        return RoleConfig(settings.reasoning_base_url, settings.reasoning_model, settings.reasoning_api_key)
    if role == "vision":
        return RoleConfig(settings.vision_base_url, settings.vision_model, settings.vision_api_key)
    raise ValueError(f"unknown LLM role: {role}")


def make_client(settings: Settings, role: Role) -> OpenAI:
    cfg = role_config(settings, role)
    # Explicit timeout: without one, a stalled/hung connection to the
    # externally-served endpoint blocks a document's processing
    # indefinitely (the OpenAI SDK's own default is 10 minutes, which is
    # both too long to fail fast and, in practice, not actually enough to
    # explain a hang observed well past that mark — worth bounding
    # explicitly rather than relying on the SDK default either way).
    return OpenAI(base_url=cfg.base_url, api_key=cfg.api_key, timeout=settings.llm_request_timeout_seconds)


def vision_chat(settings: Settings, *, image_b64: str, prompt: str, mime_type: str = "image/png") -> str:
    """One VLM call over a single (typically cropped) region image — the
    generalization of the PoC's ``call_vlm_with_image``."""
    client = make_client(settings, "vision")
    cfg = role_config(settings, "vision")
    response = client.chat.completions.create(
        model=cfg.model,
        temperature=0,
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {"type": "image_url", "image_url": {"url": f"data:{mime_type};base64,{image_b64}"}},
                ],
            }
        ],
    )
    return response.choices[0].message.content or ""
