"""Ports for validation categories (d) and (e). Dependency-inverted so rules
never talk to Postgres or an external system/MCP server directly — this is
what makes ``reference_data_rules.py``/``external_system_rules.py`` testable
with in-memory doubles."""

from __future__ import annotations

from typing import Protocol


class ReferenceDataPort(Protocol):
    """Category (d): existence-in-database lookups against internal
    reference/master data. Real Postgres-backed adapter in Phase 0
    (``persistence.repositories.ReferenceDataRepository``)."""

    async def find_employee_by_code(self, employee_code: str) -> dict | None: ...

    async def list_active_employee_names(self) -> list[tuple[str, str]]:
        """Returns (employee_code, full_name) pairs — used by fuzzy lookups
        (category d) when matching is by name rather than exact code."""
        ...


class ExternalSystemPort(Protocol):
    """Category (e): verification against a system the platform doesn't own,
    via a direct API call or an MCP tool call. Phase 0 injects a stub/
    test-double; a real adapter (a vetted MCP server) is a Phase 1+ milestone
    (roadmap item 2) — the port is defined and inject-able now so that
    milestone is additive, not a redesign."""

    async def verify(self, *, system: str, query: dict) -> dict: ...


class InMemoryReferenceDataPort:
    """Phase 0 test double / seed adapter — a plain in-memory dict, useful
    for unit tests that shouldn't need Postgres."""

    def __init__(self, employees: dict[str, str] | None = None) -> None:
        self._employees = employees or {}

    async def find_employee_by_code(self, employee_code: str) -> dict | None:
        name = self._employees.get(employee_code)
        return {"employee_code": employee_code, "full_name": name} if name else None

    async def list_active_employee_names(self) -> list[tuple[str, str]]:
        return list(self._employees.items())


class StubExternalSystemPort:
    """Phase 0 test double for category (e) — always returns a canned
    response; swapped for a real MCP-backed adapter in Fase 1+."""

    def __init__(self, canned_response: dict | None = None) -> None:
        self._canned_response = canned_response or {"verified": False, "reason": "external_system_port_not_configured"}

    async def verify(self, *, system: str, query: dict) -> dict:
        return self._canned_response
