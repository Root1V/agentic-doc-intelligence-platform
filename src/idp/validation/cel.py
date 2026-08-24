"""Thin wrapper around celpy (cel-python) — the sandboxed, side-effect-free,
guaranteed-to-terminate expression language backing kind="cel" rows in
validation_rule_definitions. Nothing outside this module + rules/generic.py
+ the validation-rules API route (compile-time check) needs to import
celpy directly.

CRITICAL: a plain nested Python dict does NOT support CEL field selection
(doc.gross_pay raises CELEvalError), and has() on one silently resolves to
False instead of raising — verified empirically. Always build activations
through celpy.json_to_cel(), never pass a raw dict straight to
Runner.evaluate()."""

from __future__ import annotations

from typing import Any

import celpy


class CelCompileError(Exception):
    """A CEL expression failed to parse. Raised by compile_expression() —
    callers never need to import celpy directly or catch celpy's own
    exception types."""


class CelEvaluationError(Exception):
    """A compiled CEL expression failed at evaluation time (e.g. an
    undeclared-reference error from a field genuinely absent even after
    has()-gating, or a type mismatch). Caught by DataDrivenRule.evaluate
    and turned into a skipped ('regla omitida') ValidationResult — the
    same graceful-degradation convention as self_rules.py's missing-field
    checks, just triggered from CEL instead of a Python `is None` check."""


_ENV = celpy.Environment()  # stateless; safe as a module-level singleton


def compile_expression(expr: str) -> celpy.Runner:
    """Compiles a CEL expression string into an executable program. Used
    both at PATCH/create-time (validation_rules.py route, before
    persisting a condition_cel/applies_when_cel string) and at
    construction-time (DataDrivenRule.__init__, once per rule instance —
    see generic.py for why this isn't recompiled per evaluate() call)."""
    try:
        ast = _ENV.compile(expr)
        return _ENV.program(ast)
    except celpy.CELParseError as exc:
        raise CelCompileError(str(exc)) from exc


def evaluate(program: celpy.Runner, variables: dict[str, Any]) -> Any:
    """variables: plain nested dict/list/scalar Python values (e.g.
    {"doc": {...}, "request": {...}}) — converted via celpy.json_to_cel so
    has()/field-selection/matches()/comprehension macros behave
    correctly."""
    activation = celpy.json_to_cel(variables)
    try:
        return program.evaluate(activation)
    except celpy.CELEvalError as exc:
        raise CelEvaluationError(str(exc)) from exc
