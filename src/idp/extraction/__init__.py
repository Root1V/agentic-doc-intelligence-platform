"""Importing concrete extractor modules here — rather than requiring every
caller to remember to do it — is what actually runs their
``@register_extractor`` decorators. Without this, ``registry.get_extractor``
raises "no extractor registered" even though the modules exist on disk,
because nothing ever imported them to execute the decorator.

Order matters only in that ``registry`` must be importable first; it has no
dependency back on these, so there is no cycle.
"""

from idp.extraction import authorization_letter, generic, insurance_disclosure, loan_application, payslip  # noqa: F401
