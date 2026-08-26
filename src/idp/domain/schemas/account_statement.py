"""Target extraction schema for ``account_statement`` — an 'Estado de Cuenta'
issued by a savings-and-credit entity (caja, cooperativa) showing a member's
('socio') standing: identity, contribution balance, and the balance/progress
of their active product(s). Promoted from a real ``generic`` extraction
(2026-08-23: page 6 of '302_Cronograma subrogado-Estado de cuenta' — one of
four distinct logical documents a segmentation pass split out of a single
physical PDF)."""

from __future__ import annotations

from pydantic import BaseModel, Field

from idp.domain.envelope import Extracted


class AccountStatementSchema(BaseModel):
    entity_name: Extracted[str] | None = Field(default=None, description="Nombre de la entidad financiera que emite el estado de cuenta.")
    print_date: Extracted[str] | None = Field(default=None, description="Fecha de impresion del documento.")
    statement_date: Extracted[str] | None = Field(default=None, description="Fecha a la que corresponde el estado de cuenta ('Estado de cuenta al').")
    member_name: Extracted[str] = Field(description="Nombre completo del socio/cliente.")
    member_code: Extracted[str] | None = Field(default=None, description="Codigo de socio.")
    member_dni: Extracted[str] | None = Field(default=None, description="DNI del socio.")
    member_category: Extracted[str] | None = Field(default=None, description="Categoria del socio (p. ej. 'SOCIO - ACTIVO - NORMAL').")
    office: Extracted[str] | None = Field(default=None, description="Oficina/agencia asociada al socio, si se indica.")
    contribution_balance: Extracted[float] | None = Field(default=None, description="Saldo de aportes del socio ('Saldo Aporte').")
    product_name: Extracted[str] | None = Field(default=None, description="Nombre del producto principal (credito/ahorro) mostrado en el estado de cuenta.")
    product_amount: Extracted[float] | None = Field(default=None, description="Monto/importe original del producto.")
    product_capital_balance: Extracted[float] | None = Field(default=None, description="Saldo capital pendiente del producto.")
    product_installments_progress: Extracted[str] | None = Field(default=None, description="Avance de cuotas del producto (p. ej. '8/24'), si se indica.")
    next_discount_amount: Extracted[float] | None = Field(default=None, description="Monto del proximo descuento/cuota programada, si se indica.")
    summary: Extracted[str] | None = Field(default=None, description="Resumen breve (1-2 frases) sobre que es este documento y su contenido principal.")
