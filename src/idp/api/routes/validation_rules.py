"""POST /validation-rules/draft (LLM drafts a CEL condition from a
plain-language description), POST /validation-rules/manual (skip the LLM,
write CEL directly), GET /validation-rules (list, filterable by
kind/status), PATCH /validation-rules/{id} (edit a still-draft CEL rule,
re-validates CEL compiles on every edit), POST /validation-rules/{id}/activate
or /reject (kind="cel" only), POST /validation-rules/{id}/disable
(deactivates an already-active kind="cel" rule), and
GET/POST /validation-rules/toggles/* (on/off switch for the hardcoded
rule_ids from pipeline/orchestrator.py::build_default_rules).

Mirrors api/routes/type_suggestions.py's exact shape and its central
guarantee: PATCH only ever touches the DB row, never generates code.
Unlike document types, though, there is no separate manual code step for
activation — the generic interpreter (validation/rules/generic.py) already
exists, so activating a row makes it execute in the very next batch run.
No row is ever hard-deleted here either — "eliminar" a rule is a status
transition (disabled/rejected), same convention as the rest of this
platform."""

from __future__ import annotations

import asyncio
import uuid
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, field_validator
from sqlalchemy.ext.asyncio import AsyncSession

from idp.api.deps import get_app_settings, get_current_user, get_db_session, require_role
from idp.config import Settings
from idp.domain.rule_draft import RuleDraft
from idp.persistence.models import User, ValidationRuleDefinition
from idp.persistence.repositories import ValidationRuleRepository
from idp.pipeline.orchestrator import hardcoded_rule_metadata
from idp.validation.cel import CelCompileError, compile_expression
from idp.validation.rule_discovery import draft_rule

router = APIRouter(prefix="/validation-rules", tags=["validation-rules"], dependencies=[Depends(get_current_user)])


class ValidationRuleResponse(BaseModel):
    id: uuid.UUID
    kind: str
    rule_id: str
    category: str
    document_type: str | None
    field_path: str | None
    description_nl: str | None
    condition_cel: str | None
    applies_when_cel: str | None
    severity: str | None
    message_pass: str | None
    message_fail: str | None
    rationale: str | None
    status: str
    created_by: str | None
    reviewer_identity: str | None


def _to_response(row: ValidationRuleDefinition) -> ValidationRuleResponse:
    return ValidationRuleResponse(
        id=row.id,
        kind=row.kind,
        rule_id=row.rule_id,
        category=row.category,
        document_type=row.document_type,
        field_path=row.field_path,
        description_nl=row.description_nl,
        condition_cel=row.condition_cel,
        applies_when_cel=row.applies_when_cel,
        severity=row.severity,
        message_pass=row.message_pass,
        message_fail=row.message_fail,
        rationale=row.rationale,
        status=row.status,
        created_by=row.created_by,
        reviewer_identity=row.reviewer_identity,
    )


def _validate_cel_or_400(condition_cel: str, applies_when_cel: str | None) -> None:
    try:
        compile_expression(condition_cel)
        if applies_when_cel:
            compile_expression(applies_when_cel)
    except CelCompileError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"expresion CEL invalida: {exc}") from exc


class DraftRuleRequest(BaseModel):
    description: str
    document_type: str
    category: Literal["self", "request_input", "reference_data"]
    field_path: str | None = None
    existing_fields_hint: list[str] | None = None

    @field_validator("description")
    @classmethod
    def _not_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("description cannot be blank")
        return value


class ManualRuleRequest(BaseModel):
    """The 'skip the LLM' power-user path — a human types CEL directly."""

    rule_id_suffix: str
    document_type: str
    category: Literal["self", "request_input", "reference_data"]
    field_path: str | None = None
    condition_cel: str
    applies_when_cel: str | None = None
    severity: Literal["info", "warning", "error"]
    message_pass: str
    message_fail: str
    rationale: str | None = None


@router.post("/draft", response_model=ValidationRuleResponse, dependencies=[Depends(require_role("operador", "admin"))])
async def draft_new_rule(
    body: DraftRuleRequest,
    settings: Settings = Depends(get_app_settings),
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
) -> ValidationRuleResponse:
    proposal: RuleDraft = await asyncio.to_thread(
        draft_rule,
        settings,
        description=body.description,
        document_type=body.document_type,
        category=body.category,
        field_path=body.field_path,
        existing_fields_hint=body.existing_fields_hint,
    )
    _validate_cel_or_400(proposal.condition_cel, proposal.applies_when_cel)

    repo = ValidationRuleRepository(session)
    rule_id = f"custom.{body.document_type}.{uuid.uuid4().hex[:8]}"
    row = await repo.create_cel_draft(
        rule_id=rule_id,
        category=body.category,
        document_type=body.document_type,
        field_path=body.field_path,
        description_nl=body.description,
        condition_cel=proposal.condition_cel,
        applies_when_cel=proposal.applies_when_cel,
        severity=proposal.severity,
        message_pass=proposal.message_pass,
        message_fail=proposal.message_fail,
        rationale=proposal.rationale,
        created_by=current_user.name,
    )
    await session.commit()
    return _to_response(row)


@router.post("/manual", response_model=ValidationRuleResponse, dependencies=[Depends(require_role("operador", "admin"))])
async def create_manual_rule(
    body: ManualRuleRequest,
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
) -> ValidationRuleResponse:
    _validate_cel_or_400(body.condition_cel, body.applies_when_cel)
    repo = ValidationRuleRepository(session)
    rule_id = f"custom.{body.document_type}.{body.rule_id_suffix}"
    if await repo.get_by_rule_id(rule_id) is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="rule_id already exists")
    row = await repo.create_cel_draft(
        rule_id=rule_id,
        category=body.category,
        document_type=body.document_type,
        field_path=body.field_path,
        description_nl=None,
        condition_cel=body.condition_cel,
        applies_when_cel=body.applies_when_cel,
        severity=body.severity,
        message_pass=body.message_pass,
        message_fail=body.message_fail,
        rationale=body.rationale,
        created_by=current_user.name,
    )
    await session.commit()
    return _to_response(row)


@router.get("", response_model=list[ValidationRuleResponse])
async def list_rules(
    kind: str | None = None,
    status_filter: str | None = None,
    session: AsyncSession = Depends(get_db_session),
) -> list[ValidationRuleResponse]:
    repo = ValidationRuleRepository(session)
    rows = await (repo.list_by_status(status_filter, kind=kind) if status_filter else repo.list_all(kind=kind))
    return [_to_response(row) for row in rows]


class UpdateRuleRequest(BaseModel):
    condition_cel: str | None = None
    applies_when_cel: str | None = None
    severity: Literal["info", "warning", "error"] | None = None
    message_pass: str | None = None
    message_fail: str | None = None
    field_path: str | None = None


@router.patch("/{definition_id}", response_model=ValidationRuleResponse, dependencies=[Depends(require_role("operador", "admin"))])
async def update_rule(
    definition_id: uuid.UUID,
    body: UpdateRuleRequest,
    session: AsyncSession = Depends(get_db_session),
) -> ValidationRuleResponse:
    repo = ValidationRuleRepository(session)
    row = await repo.get(definition_id)
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="rule not found")
    if row.status != "draft":
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="only a draft rule can be edited")

    effective_condition = body.condition_cel if body.condition_cel is not None else row.condition_cel
    effective_gate = body.applies_when_cel if body.applies_when_cel is not None else row.applies_when_cel
    if effective_condition is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="condition_cel is required")
    _validate_cel_or_400(effective_condition, effective_gate)

    row = await repo.update_draft(
        definition_id,
        condition_cel=body.condition_cel,
        applies_when_cel=body.applies_when_cel,
        severity=body.severity,
        message_pass=body.message_pass,
        message_fail=body.message_fail,
        field_path=body.field_path,
    )
    await session.commit()
    return _to_response(row)


async def _resolve(definition_id: uuid.UUID, decision: str, reviewer_identity: str, session: AsyncSession) -> ValidationRuleResponse:
    repo = ValidationRuleRepository(session)
    row = await repo.get(definition_id)
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="rule not found")
    if row.status != "draft":
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="only a draft rule can be activated or rejected")
    if decision == "active":
        if row.condition_cel is None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="condition_cel is required")
        _validate_cel_or_400(row.condition_cel, row.applies_when_cel)  # defense in depth — should already be valid
    row = await repo.set_status(definition_id, status=decision, reviewer_identity=reviewer_identity)
    await session.commit()
    return _to_response(row)


@router.post("/{definition_id}/activate", response_model=ValidationRuleResponse, dependencies=[Depends(require_role("operador", "admin"))])
async def activate_rule(
    definition_id: uuid.UUID,
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
) -> ValidationRuleResponse:
    return await _resolve(definition_id, "active", current_user.name, session)


@router.post("/{definition_id}/reject", response_model=ValidationRuleResponse, dependencies=[Depends(require_role("operador", "admin"))])
async def reject_rule(
    definition_id: uuid.UUID,
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
) -> ValidationRuleResponse:
    return await _resolve(definition_id, "rejected", current_user.name, session)


@router.post("/{definition_id}/disable", response_model=ValidationRuleResponse, dependencies=[Depends(require_role("operador", "admin"))])
async def disable_active_rule(
    definition_id: uuid.UUID,
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
) -> ValidationRuleResponse:
    repo = ValidationRuleRepository(session)
    row = await repo.get(definition_id)
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="rule not found")
    if row.status != "active":
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="only an active rule can be disabled")
    row = await repo.set_status(definition_id, status="disabled", reviewer_identity=current_user.name)
    await session.commit()
    return _to_response(row)


# --- Toggle endpoints for the hardcoded rule_ids ----------------------------


class ToggleRuleResponse(BaseModel):
    rule_id: str
    category: str
    description: str
    status: str  # "active" | "disabled"


@router.get("/toggles", response_model=list[ToggleRuleResponse])
async def list_toggles(
    settings: Settings = Depends(get_app_settings),
    session: AsyncSession = Depends(get_db_session),
) -> list[ToggleRuleResponse]:
    repo = ValidationRuleRepository(session)
    existing = {row.rule_id: row for row in await repo.list_all(kind="toggle")}
    return [
        ToggleRuleResponse(
            rule_id=rule_id,
            category=category,
            description=description,
            status=existing[rule_id].status if rule_id in existing else "active",
        )
        for rule_id, category, description in hardcoded_rule_metadata(settings)
    ]


async def _set_toggle(rule_id: str, decision: str, settings: Settings, session: AsyncSession, current_user: User) -> ToggleRuleResponse:
    metadata = {rid: (category, description) for rid, category, description in hardcoded_rule_metadata(settings)}
    if rule_id not in metadata:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="unknown hardcoded rule_id")
    category, description = metadata[rule_id]
    repo = ValidationRuleRepository(session)
    row = await repo.get_or_create_toggle(rule_id=rule_id, category=category)
    row = await repo.set_status(row.id, status=decision, reviewer_identity=current_user.name)
    await session.commit()
    return ToggleRuleResponse(rule_id=row.rule_id, category=row.category, description=description, status=row.status)


@router.post("/toggles/{rule_id:path}/disable", response_model=ToggleRuleResponse, dependencies=[Depends(require_role("operador", "admin"))])
async def disable_hardcoded_rule(
    rule_id: str,
    settings: Settings = Depends(get_app_settings),
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
) -> ToggleRuleResponse:
    return await _set_toggle(rule_id, "disabled", settings, session, current_user)


@router.post("/toggles/{rule_id:path}/enable", response_model=ToggleRuleResponse, dependencies=[Depends(require_role("operador", "admin"))])
async def enable_hardcoded_rule(
    rule_id: str,
    settings: Settings = Depends(get_app_settings),
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
) -> ToggleRuleResponse:
    return await _set_toggle(rule_id, "active", settings, session, current_user)
