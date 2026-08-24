"""Value objects for the type-discovery step: when a document falls into
``generic``, this is the LLM's structured judgment about whether its
content looks like a stable, recurring business document type worth
promoting to a first-class ``DocumentType`` — the same call a human
operator has made by hand for every type in ``domain/schemas/`` so far
(see each schema's promotion docstring). A human still decides whether to
accept the proposal (``api/routes/type_suggestions.py``); this module only
drafts it — the platform never registers a new ``DocumentType`` on its own.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

SuggestedFieldType = Literal["str", "int", "float", "bool", "list"]


class SuggestedField(BaseModel):
    name: str = Field(description="Nombre de campo en snake_case ingles, siguiendo la convencion de los esquemas existentes.")
    field_type: SuggestedFieldType
    description: str = Field(
        description=(
            "Descripcion en español de que representa el campo y de donde se extrae — debe ser explicita: "
            "en este proyecto los campos sin descripcion clara se omiten sistematicamente en la extraccion."
        )
    )
    required: bool = Field(description="Si el campo esta presente de forma consistente (True) o solo a veces (False).")


class DocumentTypeProposal(BaseModel):
    is_promotable: bool = Field(
        description=(
            "True solo si el contenido tiene una forma de negocio estable y repetible que amerite un tipo "
            "propio. False si el documento es demasiado unico, ruidoso, o su contenido no tiene una "
            "estructura clara que valga la pena estandarizar."
        )
    )
    suggested_type_name: str | None = Field(
        default=None, description="snake_case en ingles, siguiendo la convencion de los DocumentType existentes (p. ej. 'debt_capacity_calculation')."
    )
    suggested_display_name: str | None = Field(default=None, description="Nombre legible en español (p. ej. 'Calculadora de Capacidad de Endeudamiento').")
    rationale: str = Field(description="Por que este documento amerita (o no) un tipo propio, y en que se distingue de los tipos ya conocidos por la plataforma.")
    fields: list[SuggestedField] = Field(default_factory=list, description="Campos propuestos para el esquema del nuevo tipo — vacio si is_promotable es False.")
