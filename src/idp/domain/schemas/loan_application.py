"""Target extraction schema for ``loan_application`` — a Peruvian bank's
'Solicitud de Prestamo por Convenio' (payroll-agreement loan application
form): applicant personal/employment data, loan terms, and the requesting
office/officer. Promoted from a real ``generic`` extraction (2026-08-23:
BBVA 'Solicitud de Convenio', FVX0007042584) once the field set proved
stable and extractable — see ``authorization_letter.py`` for the same
promotion pattern applied earlier in this same loan file.

Field disambiguation lives in ``Field(description=...)`` rather than plain
Python comments deliberately: comments never reach the model — only
``schema_cls.model_json_schema()`` (sent verbatim in the extraction prompt)
does, and Pydantic's ``Field(description=...)`` is what shows up there.
A prose paragraph in the system prompt is easy for the model to lose track
of across many fields and tool-call turns; a description sitting right next
to its field in the schema is not.
"""

from __future__ import annotations

from pydantic import BaseModel, Field

from idp.domain.envelope import Extracted

# Prefixed applicant_* deliberately: this form also names a loan officer and
# a sales coordinator in its header/signature blocks — a plain "first_name"/
# "dni" was ambiguous enough that the agent once extracted the officer's
# identity instead of the actual applicant's (section C, 'DATOS PERSONALES
# DEL SOLICITANTE'). The field name itself is now part of the
# disambiguation, on top of the per-field description below.
_APPLICANT_NOTE = (
    "Corresponde EXCLUSIVAMENTE al titular/solicitante del prestamo (seccion 'DATOS PERSONALES DEL "
    "SOLICITANTE' o equivalente, con su firma y huella al final del documento) — nunca al asesor, "
    "coordinador o promotor comercial del banco que gestiona la solicitud (aparecen en el encabezado o "
    "pie de pagina con su propio nombre y DNI)."
)


class LoanApplicationSchema(BaseModel):
    applicant_first_name: Extracted[str] = Field(description=_APPLICANT_NOTE)
    applicant_paternal_surname: Extracted[str] = Field(description=_APPLICANT_NOTE)
    applicant_maternal_surname: Extracted[str] | None = Field(default=None, description=_APPLICANT_NOTE)
    applicant_dni: Extracted[str] | None = Field(default=None, description=_APPLICANT_NOTE)
    date_of_birth: Extracted[str] | None = None
    email: Extracted[str] | None = None
    phone_mobile: Extracted[str] | None = None

    address: Extracted[str] | None = None
    district: Extracted[str] | None = None
    province: Extracted[str] | None = None
    department: Extracted[str] | None = None

    bank: Extracted[str] | None = None
    loan_amount_requested: Extracted[float] | None = None
    loan_term_months: Extracted[int] | None = None
    grace_period_months: Extracted[int] | None = None
    payment_day: Extracted[int] | None = Field(default=None, description="Dia del mes en que se paga la cuota (no fecha completa).")
    loan_officer_name: Extracted[str] | None = Field(
        default=None, description="El asesor/coordinador de ventas del banco que gestiona la solicitud — NUNCA el titular/solicitante."
    )

    employment_center: Extracted[str] | None = None
    employment_ruc: Extracted[str] | None = None
    employment_sector: Extracted[str] | None = Field(
        default=None,
        description="El 'GIRO PRINCIPAL DEL NEGOCIO' / rubro del centro de trabajo (p. ej. SALUD, COMERCIO) — NO el puesto del solicitante.",
    )
    employment_position: Extracted[str] | None = Field(
        default=None,
        description="El 'CARGO' / puesto de trabajo del solicitante (p. ej. OBSTETRA, CONTADOR) — NO el rubro del negocio (ese es employment_sector).",
    )
    employment_start_date: Extracted[str] | None = None
    monthly_income: Extracted[float] | None = None
    dependents_count: Extracted[int] | None = None

    # Seccion N (banco) — normalmente en la ultima pagina del formulario;
    # la decision/condiciones reales del banco pueden diferir de lo
    # solicitado en la seccion A. Deliberadamente en el esquema para
    # ejercitar y verificar el grounding de pagina en documentos multi-pagina.
    approval_status: Extracted[str] | None = Field(default=None, description="Valor de 'SOLICITUD APROBADA' (SI/NO), seccion de evaluacion del banco.")
    approved_amount: Extracted[float] | None = Field(default=None, description="'MONTO A FINANCIAR' en la seccion de evaluacion del banco (puede diferir de loan_amount_requested).")
    approved_interest_rate: Extracted[str] | None = Field(default=None, description="'TASA INTERES' en la seccion de evaluacion del banco (no el '% A FINANCIAR').")
    approved_term_months: Extracted[int] | None = Field(default=None, description="'PLAZO MESES' aprobado en la seccion de evaluacion del banco.")
    summary: Extracted[str] | None = Field(default=None, description="Resumen breve (1-2 frases) sobre que es este documento y su contenido principal.")
