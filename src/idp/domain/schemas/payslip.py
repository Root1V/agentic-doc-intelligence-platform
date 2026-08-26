"""Target extraction schema for the ``payslip`` document type (boleta de pago).

This is the stable, business-known part of the extraction problem — field
names don't change even though the physical layout of a payslip does. See
``idp.extraction.agentic`` for how the layout-tolerant extraction method
fills this schema in.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

from idp.domain.envelope import Extracted

ConceptKind = Literal["earning", "deduction"]


class PayslipConcept(BaseModel):
    """One line item on a payslip (a concepto: e.g. 'Sueldo Basico', 'AFP')."""

    name: Extracted[str]
    amount: Extracted[float]
    kind: Extracted[ConceptKind]


class PayslipSchema(BaseModel):
    employee_name: Extracted[str]
    employee_code: Extracted[str] | None = Field(
        default=None, description="El codigo de empleado (p. ej. 'Codigo AIRHSP') — extraelo si esta presente, no lo omitas."
    )
    employer_name: Extracted[str] | None = Field(
        default=None, description="El campo 'Empleador' — extraelo si esta presente, no lo omitas."
    )
    period: Extracted[str]
    gross_pay: Extracted[float]
    total_deductions: Extracted[float]
    net_pay: Extracted[float]
    concepts: list[PayslipConcept] = Field(default_factory=list)
    summary: Extracted[str] | None = Field(default=None, description="Resumen breve (1-2 frases) sobre que es este documento y su contenido principal.")
