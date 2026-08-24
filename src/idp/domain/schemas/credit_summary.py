"""Target extraction schema for ``credit_summary`` — a compact one-page
credit/loan snapshot issued by a savings-and-credit entity (caja, cooperativa)
showing a member's ('socio') active credit at a glance: amount, term,
installment, rate, status. Distinct from ``loan_payment_schedule`` (which
carries the full installment-by-installment table) — this is a summary
record, not an amortization schedule. Promoted from a real ``generic``
extraction (2026-08-23: page 5 of '302_Cronograma subrogado-Estado de
cuenta' — one of four distinct logical documents a segmentation pass split
out of a single physical PDF)."""

from __future__ import annotations

from pydantic import BaseModel, Field

from idp.domain.envelope import Extracted


class CreditSummarySchema(BaseModel):
    entity_name: Extracted[str] | None = Field(default=None, description="Nombre de la entidad financiera que emite el documento.")
    print_date: Extracted[str] | None = Field(default=None, description="Fecha de impresion del documento.")
    credit_date: Extracted[str] | None = Field(default=None, description="Fecha de otorgamiento del credito.")
    member_name: Extracted[str] = Field(description="Nombre completo del socio/cliente titular del credito.")
    member_dni: Extracted[str] | None = Field(default=None, description="DNI del socio/cliente.")
    member_phone: Extracted[str] | None = Field(default=None, description="Telefono del socio/cliente, si se indica.")
    product_name: Extracted[str] | None = Field(default=None, description="Nombre comercial del producto de credito.")
    credit_amount: Extracted[float] | None = Field(default=None, description="Monto total del credito otorgado.")
    term_months: Extracted[int] | None = Field(default=None, description="Plazo del credito en meses.")
    monthly_installment: Extracted[float] | None = Field(default=None, description="Monto de la cuota mensual.")
    interest_rate: Extracted[str] | None = Field(default=None, description="Tasa de interes del credito.")
    status: Extracted[str] | None = Field(default=None, description="Estado del credito (p. ej. 'OTORGADO').")
