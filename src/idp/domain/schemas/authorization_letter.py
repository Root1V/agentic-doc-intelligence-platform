"""Target extraction schema for ``authorization_letter`` — a Peruvian
'Carta de Autorizacion' where a person authorizes a third party (typically
an employer or a bank) to act on their behalf or to deduct money from their
income, most commonly a payroll-deduction ('Descuento por Planilla')
authorization tied to a bank loan. Promoted from a real ``generic``
extraction (2026-08-23: 'ANEXO C' BBVA payroll-deduction authorization,
FVX0007042584) once the pattern proved extractable with a stable field set."""

from __future__ import annotations

from pydantic import BaseModel

from idp.domain.envelope import Extracted


class AuthorizationLetterSchema(BaseModel):
    client_name: Extracted[str]
    client_dni: Extracted[str] | None = None
    company: Extracted[str] | None = None  # empleador del titular
    bank: Extracted[str] | None = None  # entidad beneficiaria de la autorizacion
    loan_amount: Extracted[float] | None = None
    monthly_installment: Extracted[float] | None = None
    loan_term_months: Extracted[int] | None = None
    document_date: Extracted[str] | None = None
    document_place: Extracted[str] | None = None
    reference: Extracted[str] | None = None  # asunto/referencia de la carta
