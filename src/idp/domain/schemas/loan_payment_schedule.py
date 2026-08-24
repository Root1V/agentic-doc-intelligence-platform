"""Target extraction schema for ``loan_payment_schedule`` — a 'Cronograma de
Pagos' (loan amortization schedule) issued by a lending entity (bank, caja,
cooperative), with a header of loan terms plus a table of installments.
Promoted from a real ``generic`` extraction (2026-08-23: pages 2-4 of
'302_Cronograma subrogado-Estado de cuenta' — one of four distinct logical
documents a segmentation pass split out of a single physical PDF). This is
the segment that originally caused the extraction loop to time out when the
whole 7-page bundle was forced through one classify->extract pass; isolated
to its own ~3-page segment, the full installment table is small enough to
extract directly rather than only capturing header/summary fields."""

from __future__ import annotations

from pydantic import BaseModel, Field

from idp.domain.envelope import Extracted


class LoanInstallment(BaseModel):
    """One row of the amortization table."""

    number: Extracted[str] = Field(description="Numero de cuota (p. ej. '1', 'T2') tal como aparece en la tabla.")
    due_date: Extracted[str] = Field(description="Fecha de vencimiento de la cuota.")
    installment_amount: Extracted[float] = Field(description="Monto total de la cuota (columna 'Cuota + ITF' o equivalente).")
    interest_amount: Extracted[float] | None = Field(default=None, description="Componente de interes de la cuota.")
    principal_amount: Extracted[float] | None = Field(default=None, description="Componente de capital/amortizacion de la cuota.")
    remaining_balance: Extracted[float] | None = Field(default=None, description="Saldo capital pendiente despues de esta cuota.")


class LoanPaymentScheduleSchema(BaseModel):
    client_name: Extracted[str] = Field(description="Nombre completo del cliente titular del credito.")
    client_dni: Extracted[str] | None = Field(default=None, description="DNI o numero de documento del cliente.")
    entity_name: Extracted[str] | None = Field(default=None, description="Entidad financiera que emite el cronograma (p. ej. 'Caja Trujillo').")
    product_name: Extracted[str] | None = Field(default=None, description="Nombre comercial del producto de credito (p. ej. 'DISFRUTA+').")
    account_number: Extracted[str] | None = Field(default=None, description="Numero de cuenta o codigo de credito.")
    currency: Extracted[str] | None = Field(default=None, description="Moneda del credito (p. ej. 'Soles').")
    loan_amount: Extracted[float] | None = Field(default=None, description="Monto del credito desembolsado.")
    interest_rate_tea: Extracted[str] | None = Field(default=None, description="Tasa Efectiva Anual (TEA), si se menciona.")
    interest_rate_tcea: Extracted[str] | None = Field(default=None, description="Tasa de Costo Efectivo Anual (TCEA), si se menciona.")
    insurance_provider: Extracted[str] | None = Field(default=None, description="Aseguradora del seguro de desgravamen, si se menciona.")
    loan_term_installments: Extracted[int] | None = Field(default=None, description="Numero total de cuotas del credito.")
    disbursement_date: Extracted[str] | None = Field(default=None, description="Fecha de desembolso/operacion del credito.")
    total_amount_to_pay: Extracted[float] | None = Field(default=None, description="Monto total a pagar segun el cronograma, si se indica.")
    installments: list[LoanInstallment] = Field(
        default_factory=list, description="Cada fila de la tabla de cronograma de pagos, en orden — una entrada por cuota."
    )
