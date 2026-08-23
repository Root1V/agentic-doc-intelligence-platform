"""Target extraction schema for the ``insurance_disclosure`` document type —
a Peruvian 'Declaracion Personal de Seguros - Seguro de Desgravamen' (a
health declaration underwriting a loan-linked life/disability insurance),
matching the actual PoC fixture (``seguro_desgravamen.png``: RIMAC/BBVA
declaration, insured person, loan amount/term, no policy number/coverage/
premium/effective-expiration dates — those fields belong to a policy
document, not this underwriting declaration)."""

from __future__ import annotations

from pydantic import BaseModel

from idp.domain.envelope import Extracted


class InsuranceDisclosureSchema(BaseModel):
    # Split into first_name/paternal_surname/maternal_surname rather than a
    # single insured_name: the source form has these in three separate
    # boxes, and in practice the agent reliably extracts each box on its
    # own but does not reliably concatenate them into one field across
    # multiple tool-call turns (confirmed: same failure mode seen on
    # loan_application's applicant name, fixed there the same way).
    insured_first_name: Extracted[str]
    insured_paternal_surname: Extracted[str] | None = None
    insured_maternal_surname: Extracted[str] | None = None
    insured_dni: Extracted[str] | None = None
    insurer_name: Extracted[str] | None = None
    loan_amount: Extracted[float] | None = None
    loan_term_months: Extracted[int] | None = None
    insurance_type: Extracted[str] | None = None
    declaration_date: Extracted[str] | None = None
    declaration_place: Extracted[str] | None = None
