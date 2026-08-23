"""Category (c): conditional/chained validation — 'if field X (doc A)
satisfies condition C, validate field Y (same doc or another)'. This is
transversal rather than its own check logic: ``ConditionalRule`` wraps any
other rule (of any category) with an activation gate, reusing
``ValidationEngine``'s existing ``applies_when``/``depends_on`` machinery."""

from __future__ import annotations

from collections.abc import Callable

from idp.validation.base import RuleCategory, ValidationResult, ValidationRule
from idp.validation.context import ValidationContext

Condition = Callable[[ValidationContext], bool]


class ConditionalRule(ValidationRule):
    category = RuleCategory.CONDITIONAL

    def __init__(
        self,
        rule_id: str,
        condition: Condition,
        inner: ValidationRule,
        *,
        depends_on: list[str] | None = None,
    ) -> None:
        self.rule_id = rule_id
        self._condition = condition
        self._inner = inner
        self.depends_on = depends_on if depends_on is not None else list(inner.depends_on)

    def applies_when(self, context: ValidationContext) -> bool:
        return self._condition(context) and self._inner.applies_when(context)

    async def evaluate(self, context: ValidationContext) -> ValidationResult:
        result = await self._inner.evaluate(context)
        # Re-tag as this conditional rule's identity/category for reporting,
        # while keeping the inner rule's actual comparison logic untouched.
        return result.model_copy(update={"rule_id": self.rule_id, "category": self.category})
