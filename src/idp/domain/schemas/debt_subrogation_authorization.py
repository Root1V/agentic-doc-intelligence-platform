"""Target extraction schema for ``debt_subrogation_authorization`` — a
Peruvian 'AUTORIZACION PARA LA SUBROGACION DE DEUDA DE OTROS BANCOS
MEDIANTE UN PRESTAMO PERSONAL POR CONVENIO' form: the client authorizes a
bank to cancel their outstanding obligations (personal loans and/or credit
cards) held at OTHER financial entities, funded by a new personal loan.
Distinct from ``authorization_letter`` (payroll-deduction authorization,
'Descuento por Planilla'): this form's core content is a table of debts to
subrogate (creditor entity, loan/card number, currency, amount) — fields
``authorization_letter`` has no place for. Promoted from a real
``authorization_letter`` extraction (2026-08-23: pages 0-3 of
'332_Carta de instruccion de compra de deuda', where the debt table was
being silently dropped) once the schema mismatch made clear this is a
distinct document type."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

from idp.domain.envelope import Extracted

DebtKind = Literal["loan", "credit_card"]


class SubrogatedDebt(BaseModel):
    """One row of the 'DETALLE DE LA DEUDA A SUBROGAR' table — either the
    'PRESTAMOS' or the 'TARJETAS DE CREDITO' section."""

    debt_kind: Extracted[DebtKind] = Field(description="'loan' si viene de la seccion PRESTAMOS, 'credit_card' si viene de TARJETAS DE CREDITO.")
    entity_name: Extracted[str] = Field(description="Entidad financiera acreedora de esta deuda.")
    reference_number: Extracted[str] | None = Field(default=None, description="Numero de prestamo o de tarjeta de credito.")
    currency: Extracted[str] | None = Field(default=None, description="Moneda de la deuda (p. ej. 'S/.' o 'US$').")
    amount_soles: Extracted[float] = Field(description="Monto de la deuda, en soles.")


class DebtSubrogationAuthorizationSchema(BaseModel):
    client_name: Extracted[str]
    client_dni: Extracted[str] | None = None
    client_address: Extracted[str] | None = None
    client_phone: Extracted[str] | None = Field(default=None, description="Telefono fijo o celular del cliente, si se indica.")
    client_email: Extracted[str] | None = None
    document_date: Extracted[str] | None = None
    bank: Extracted[str] | None = Field(default=None, description="Banco que otorga el nuevo prestamo y asume la subrogacion (el emisor del formulario, p. ej. 'BBVA').")
    debts: list[SubrogatedDebt] = Field(
        default_factory=list,
        description="Cada fila NO VACIA de las tablas 'PRESTAMOS' y 'TARJETAS DE CREDITO' — no incluyas filas sin entidad/monto.",
    )
    total_debt_amount: Extracted[float] | None = Field(default=None, description="'TOTAL DEUDA A SUBROGAR', en soles.")
    new_loan_amount: Extracted[float] | None = Field(default=None, description="Monto del nuevo prestamo personal ('MONTO PRESTAMO'), si se indica.")
    deposit_account_number: Extracted[str] | None = Field(
        default=None, description="Numero de la 'CUENTA DE DEPOSITO' donde se desembolsaria el nuevo prestamo, si el cliente la indico."
    )
    summary: Extracted[str] | None = Field(default=None, description="Resumen breve (1-2 frases) sobre que es este documento y su contenido principal.")
