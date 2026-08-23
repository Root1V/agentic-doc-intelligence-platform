"""Intra-document deterministic checks — arithmetic/date/format consistency
within a single document. Never an LLM call, per the cross-cutting
'deterministic core' principle: correctness-critical math stays in plain
Python."""

from __future__ import annotations

from idp.validation.base import ConfidenceMethod, RuleCategory, Severity, ValidationResult, ValidationRule
from idp.validation.context import ValidationContext

_TOLERANCE = 0.01


class PayslipArithmeticConsistency(ValidationRule):
    rule_id = "self.payslip_arithmetic_consistency"
    category = RuleCategory.SELF

    def applies_when(self, context: ValidationContext) -> bool:
        return context.current_document.document_type == "payslip"

    async def evaluate(self, context: ValidationContext) -> ValidationResult:
        fields = context.current_document.fields
        gross = fields.get("gross_pay")
        deductions = fields.get("total_deductions")
        net = fields.get("net_pay")

        if gross is None or deductions is None or net is None:
            return ValidationResult(
                rule_id=self.rule_id,
                category=self.category,
                passed=True,
                message="Campos insuficientes para verificar aritmetica; regla omitida.",
                confidence=1.0,
                confidence_method=ConfidenceMethod.DETERMINISTIC,
                explanation="gross_pay, total_deductions o net_pay ausente en la extraccion.",
            )

        expected_net = round(gross - deductions, 2)
        passed = abs(expected_net - net) <= _TOLERANCE
        return ValidationResult(
            rule_id=self.rule_id,
            category=self.category,
            passed=passed,
            severity=None if passed else Severity.ERROR,
            field_path="net_pay",
            message="gross_pay - total_deductions coincide con net_pay." if passed else "gross_pay - total_deductions no coincide con net_pay.",
            expected=expected_net,
            actual=net,
            confidence=1.0,
            confidence_method=ConfidenceMethod.DETERMINISTIC,
            explanation=f"gross_pay({gross}) - total_deductions({deductions}) = {expected_net} vs net_pay extraido = {net} (tolerancia {_TOLERANCE}).",
        )


class DniFormatValid(ValidationRule):
    """DNI peruano: exactamente 8 digitos numericos. Parametrizada por
    document_type + nombre de campo en vez de una clase por tipo de
    documento — cada tipo nuevo con un campo de DNI solo necesita
    instanciar esta regla, no duplicarla (ver ``pipeline/orchestrator.py``)."""

    category = RuleCategory.SELF

    def __init__(self, document_type: str, field_name: str) -> None:
        self._document_type = document_type
        self._field_name = field_name
        self.rule_id = f"self.{document_type}_dni_format_valid"

    def applies_when(self, context: ValidationContext) -> bool:
        return context.current_document.document_type == self._document_type

    async def evaluate(self, context: ValidationContext) -> ValidationResult:
        fields = context.current_document.fields
        dni = fields.get(self._field_name)

        if not dni:
            return ValidationResult(
                rule_id=self.rule_id,
                category=self.category,
                passed=True,
                message=f"{self._field_name} ausente; regla omitida.",
                confidence=1.0,
                confidence_method=ConfidenceMethod.DETERMINISTIC,
                explanation=f"{self._field_name} no fue extraido del documento.",
            )

        passed = str(dni).isdigit() and len(str(dni)) == 8
        return ValidationResult(
            rule_id=self.rule_id,
            category=self.category,
            passed=passed,
            severity=None if passed else Severity.ERROR,
            field_path=self._field_name,
            message=f"{self._field_name} tiene formato valido (8 digitos)." if passed else f"{self._field_name} no tiene formato valido (se esperan 8 digitos).",
            actual=dni,
            confidence=1.0,
            confidence_method=ConfidenceMethod.DETERMINISTIC,
            explanation=f"Verificacion de formato: {self._field_name}={dni!r}, longitud={len(str(dni))}.",
        )
