"""What a ``ValidationRule`` can read: the current document's extracted
fields, its sibling documents' extracted fields within the same request,
the request's raw input payload, the injected ports, and the results of
already-evaluated rules this run (so conditional rules — category c — can
read what they depend on)."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import Any

from idp.domain.request_payload import RequestInputPayload
from idp.validation.base import ValidationResult
from idp.validation.ports import ExternalSystemPort, ReferenceDataPort


@dataclass
class DocumentFields:
    document_id: uuid.UUID
    document_type: str
    fields: dict[str, Any]  # flattened field_path -> raw value (already unwrapped from Extracted[T])


@dataclass
class ValidationContext:
    batch_id: uuid.UUID
    current_document: DocumentFields
    sibling_documents: list[DocumentFields]
    request_payload: RequestInputPayload
    reference_data: ReferenceDataPort
    external_system: ExternalSystemPort
    rule_results: dict[str, ValidationResult] = field(default_factory=dict)

    def result_of(self, rule_id: str) -> ValidationResult | None:
        return self.rule_results.get(rule_id)
