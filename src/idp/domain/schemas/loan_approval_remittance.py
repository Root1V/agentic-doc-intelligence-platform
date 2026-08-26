"""Target extraction schema for ``loan_approval_remittance`` — a short,
single-section internal record ('Remesa') generated once a loan case has
been approved by HR ('APROBADO - RRHH') and is queued for disbursement.
Distinct from ``loan_application`` (the multi-page, multi-section intake
form): this is a compact status/approval snapshot with no personal,
employment, spouse or patrimony sections. Promoted from a real
``loan_application`` extraction (2026-08-23: '93_Remesa_FVX0007040373',
17 of 21 fields null and 'Plaza' misread into employment_center) once the
schema mismatch made clear this is a distinct document type."""

from __future__ import annotations

from pydantic import BaseModel, Field

from idp.domain.envelope import Extracted


class LoanApprovalRemittanceSchema(BaseModel):
    applicant_dni: Extracted[str] = Field(description="'Documento de identidad'.")
    applicant_first_name: Extracted[str] = Field(description="Nombre(s) de pila, del campo 'Nombre Completo'.")
    applicant_paternal_surname: Extracted[str] = Field(description="Apellido paterno, del campo 'Nombre Completo'.")
    applicant_maternal_surname: Extracted[str] | None = Field(
        default=None, description="Apellido materno, del campo 'Nombre Completo' — extraelo si esta presente, no lo omitas."
    )
    email: Extracted[str] | None = Field(default=None, description="'Correo' del solicitante — extraelo si esta presente, no lo omitas.")
    phone_mobile: Extracted[str] | None = Field(default=None, description="'Celular' del solicitante — extraelo si esta presente, no lo omitas.")
    approval_status: Extracted[str] = Field(description="El campo 'Estado' (p. ej. 'APROBADO - RRHH').")
    requested_amount: Extracted[float] = Field(description="'Importe Solicitado'.")
    monthly_installment: Extracted[float] | None = Field(default=None, description="'Monto de Cuota'.")
    approval_date: Extracted[str] | None = Field(default=None, description="'Fecha de aprobacion de RRHH'.")
    office: Extracted[str] | None = Field(
        default=None, description="El campo 'Plaza' (sede/region de la oficina que gestiona el caso, no el centro de trabajo del solicitante)."
    )
    entry_date: Extracted[str] | None = Field(default=None, description="'Fecha de ingreso' del caso al sistema.")
    position: Extracted[str] | None = Field(default=None, description="'Cargo', si esta presente.")
    summary: Extracted[str] | None = Field(default=None, description="Resumen breve (1-2 frases) sobre que es este documento y su contenido principal.")
