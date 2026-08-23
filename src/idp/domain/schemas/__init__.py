"""Maps ``DocumentType`` to its target extraction schema — the single source
of truth the orchestrator uses to re-validate a persisted extraction payload
back into a typed schema instance (e.g. for review-candidate routing).
Without this, code that hardcodes 'payslip or else insurance_disclosure'
breaks silently for any other document type, including ``generic``."""

from __future__ import annotations

from pydantic import BaseModel

from idp.domain.document_types import DocumentType
from idp.domain.schemas.authorization_letter import AuthorizationLetterSchema
from idp.domain.schemas.generic import GenericSchema
from idp.domain.schemas.insurance_disclosure import InsuranceDisclosureSchema
from idp.domain.schemas.loan_application import LoanApplicationSchema
from idp.domain.schemas.payslip import PayslipSchema

SCHEMA_BY_DOCUMENT_TYPE: dict[DocumentType, type[BaseModel]] = {
    DocumentType.PAYSLIP: PayslipSchema,
    DocumentType.INSURANCE_DISCLOSURE: InsuranceDisclosureSchema,
    DocumentType.AUTHORIZATION_LETTER: AuthorizationLetterSchema,
    DocumentType.LOAN_APPLICATION: LoanApplicationSchema,
    DocumentType.GENERIC: GenericSchema,
}


def schema_for(document_type: DocumentType | str) -> type[BaseModel]:
    key = DocumentType(document_type) if not isinstance(document_type, DocumentType) else document_type
    return SCHEMA_BY_DOCUMENT_TYPE[key]
