"""The closed set of document types this platform knows how to classify and
extract. Adding a new type means: add an enum value here, add a schema in
``domain/schemas/``, add an extractor registered in ``extraction/registry.py``,
and add classification examples — nothing else in the pipeline changes.
"""

from __future__ import annotations

from enum import StrEnum


class DocumentType(StrEnum):
    PAYSLIP = "payslip"
    INSURANCE_DISCLOSURE = "insurance_disclosure"
    AUTHORIZATION_LETTER = "authorization_letter"
    LOAN_APPLICATION = "loan_application"
    GENERIC = "generic"
