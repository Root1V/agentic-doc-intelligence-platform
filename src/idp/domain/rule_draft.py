"""Value object for the rule-discovery step: the LLM's structured draft of
a CEL condition + human-facing messages from a plain-language description.
A human still reviews/edits/activates it
(api/routes/validation_rules.py) — this module only drafts it, mirroring
domain/type_suggestion.py's DocumentTypeProposal for document types.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

RuleSeverity = Literal["info", "warning", "error"]


class RuleDraft(BaseModel):
    condition_cel: str = Field(
        description=(
            "Expresion CEL (Common Expression Language) que evalua la condicion. Variables disponibles: "
            "doc.<campo>, request.<campo>, y si la categoria es 'reference_data' tambien "
            "reference_data.employee_code_exists (booleano precalculado)."
        )
    )
    applies_when_cel: str | None = Field(
        default=None,
        description=(
            "Expresion CEL opcional adicional (solo doc./request., nunca reference_data.) que debe cumplirse "
            "para que la regla aplique, mas alla del tipo de documento. None si no aplica."
        ),
    )
    severity: RuleSeverity = Field(description="Severidad cuando la condicion NO se cumple.")
    message_pass: str = Field(description="Mensaje en español cuando la condicion se cumple.")
    message_fail: str = Field(description="Mensaje en español cuando la condicion NO se cumple.")
    rationale: str = Field(
        description="Explicacion breve de la logica de la expresion CEL generada, para que un humano la pueda revisar."
    )
