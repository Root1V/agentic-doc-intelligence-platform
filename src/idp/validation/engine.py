"""The ValidationEngine: given a set of registered rules, builds a
dependency graph from ``depends_on`` and executes it in topological order —
not a flat list — so a conditional rule can read the result of the rule it
depends on before deciding whether to activate."""

from __future__ import annotations

from idp.observability.otel import traced_validation_rule
from idp.validation.base import ValidationResult, ValidationRule
from idp.validation.context import ValidationContext


class CyclicDependencyError(Exception):
    pass


def _topological_order(rules: list[ValidationRule]) -> list[ValidationRule]:
    by_id = {r.rule_id: r for r in rules}
    visited: set[str] = set()
    temp_mark: set[str] = set()
    ordered: list[ValidationRule] = []

    def visit(rule: ValidationRule) -> None:
        if rule.rule_id in visited:
            return
        if rule.rule_id in temp_mark:
            raise CyclicDependencyError(f"cycle involving rule {rule.rule_id!r}")
        temp_mark.add(rule.rule_id)
        for dep_id in rule.depends_on:
            dep = by_id.get(dep_id)
            if dep is not None:
                visit(dep)
        temp_mark.discard(rule.rule_id)
        visited.add(rule.rule_id)
        ordered.append(rule)

    for rule in rules:
        visit(rule)
    return ordered


async def run_validation(rules: list[ValidationRule], context: ValidationContext) -> list[ValidationResult]:
    results: list[ValidationResult] = []
    for rule in _topological_order(rules):
        if not rule.applies_when(context):
            continue
        with traced_validation_rule(rule_id=rule.rule_id, category=rule.category.value):
            result = await rule.evaluate(context)
        context.rule_results[rule.rule_id] = result
        results.append(result)
    return results
