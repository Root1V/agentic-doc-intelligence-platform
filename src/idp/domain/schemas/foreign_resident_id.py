"""Target extraction schema for ``foreign_resident_id`` — a scanned copy of
one or more 'Carnet de Extranjeria' (foreign-resident ID card, Peru) records,
typically attached as a KYC/identity document within a loan file. A single
scan can contain records for more than one person (e.g. a couple), so the
schema is a list rather than a flat record — same shape as ``PayslipConcept``.
Promoted from a real ``generic`` extraction (2026-08-23: '105_Carnet-
extranjeria_001520058', two Chilean nationals' ID records) once the pattern
proved extractable with a stable field set."""

from __future__ import annotations

from pydantic import BaseModel, Field

from idp.domain.envelope import Extracted


class ForeignResidentIdentity(BaseModel):
    """One person's identity record within the scanned document."""

    surnames: Extracted[str] = Field(description="'APELLIDOS'.")
    first_names: Extracted[str] = Field(description="'NOMBRES'.")
    nationality: Extracted[str] | None = Field(default=None, description="'NACIONALIDAD'.")
    date_of_birth: Extracted[str] | None = Field(default=None, description="'NACIMIENTO'.")
    gender: Extracted[str] | None = Field(default=None, description="'SEXO'.")
    marital_status: Extracted[str] | None = Field(default=None, description="'ESTADO CIVIL', si esta presente.")
    foreigner_id_number: Extracted[str] = Field(description="'CARNE DE EXTRANJERIA N°'.")
    passport_number: Extracted[str] | None = Field(default=None, description="'N° Pasaporte'.")
    inscription_date: Extracted[str] | None = Field(default=None, description="'Fec Inscripcion'.")
    issue_date: Extracted[str] | None = Field(default=None, description="'Fec Emision'.")
    expiration_date: Extracted[str] | None = Field(default=None, description="'Vencimiento'.")


class ForeignResidentIdSchema(BaseModel):
    persons: list[ForeignResidentIdentity] = Field(
        default_factory=list,
        description="Una entrada por cada persona cuyo carne de extranjeria aparece en el documento — puede haber mas de una.",
    )
    summary: Extracted[str] | None = Field(default=None, description="Resumen breve (1-2 frases) sobre que es este documento y su contenido principal.")
