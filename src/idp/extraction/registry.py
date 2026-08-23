"""Strategy pattern: maps ``DocumentType`` to the extractor that handles it.
Adding a document type never touches ``pipeline/orchestrator.py`` — only
this registry and the new schema/extractor modules."""

from __future__ import annotations

from idp.domain.document_types import DocumentType
from idp.extraction.base import BaseExtractor

_REGISTRY: dict[DocumentType, BaseExtractor] = {}


def register_extractor(document_type: DocumentType):
    def decorator(cls: type[BaseExtractor]) -> type[BaseExtractor]:
        _REGISTRY[document_type] = cls()
        return cls

    return decorator


def get_extractor(document_type: DocumentType) -> BaseExtractor:
    try:
        return _REGISTRY[document_type]
    except KeyError as exc:
        raise ValueError(f"no extractor registered for document_type={document_type}") from exc
