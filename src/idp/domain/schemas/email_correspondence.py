"""Target extraction schema for ``email_correspondence`` — a generic email
found within a document bundle (e.g. an internal email forwarded as part of
a loan file's attachments). Deliberately broad rather than specific to any
one email's business purpose: the first real example seen was a credit-
bureau debt inquiry, but the next one could be about something else
entirely (an approval, a general request) — hard-coding that example's
specific fields (referenced_entity, risk_classification, ...) would not
have generalized (replaces the single-example ``risk_inquiry_email`` type,
2026-08-23). Universal email metadata is captured as real fields; whatever
business content the email carries goes into ``key_facts`` (same flexible
key/value shape as ``generic.py``) instead of a fixed schema. Promote a
specific email sub-type (e.g. risk-inquiry emails) once several real
examples justify it."""

from __future__ import annotations

from pydantic import BaseModel, Field

from idp.domain.envelope import Extracted


class EmailKeyFact(BaseModel):
    """One business-relevant fact pulled from the email body — same
    flexible key/value shape as ``generic.GenericField``, since an email's
    content varies far more than this platform's other document types."""

    key: str
    value: Extracted[str]


class EmailCorrespondenceSchema(BaseModel):
    sender_name: Extracted[str] = Field(description="Nombre de quien envia el correo.")
    sender_email: Extracted[str] | None = Field(default=None, description="Correo electronico del remitente.")
    recipient_name: Extracted[str] | None = Field(default=None, description="Nombre del destinatario principal.")
    cc_name: Extracted[str] | None = Field(default=None, description="Nombre en copia (CC), si se indica.")
    date: Extracted[str] | None = Field(default=None, description="Fecha del correo.")
    subject: Extracted[str] | None = Field(default=None, description="Asunto del correo, si se indica.")
    body_summary: Extracted[str] | None = Field(
        default=None, description="Resumen breve en tus propias palabras del proposito y contenido del correo."
    )
    key_facts: list[EmailKeyFact] = Field(
        default_factory=list,
        description=(
            "Datos relevantes de negocio mencionados en el cuerpo del correo (p. ej. nombre y DNI de un "
            "cliente referido, un monto, una entidad) — uno por cada dato distinto, como pares clave/valor "
            "libres. No asumas de antemano que tipo de dato de negocio contiene el correo."
        ),
    )
