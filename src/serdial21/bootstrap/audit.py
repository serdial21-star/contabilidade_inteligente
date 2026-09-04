'''Composição do commit hook de auditoria para mutações já aprovadas.'''

from collections.abc import Generator
from contextlib import contextmanager
from dataclasses import dataclass
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import event, inspect
from sqlalchemy.orm import Session

from serdial21.modules.access_control.adapters.outbound.persistence.models import (
    CompanyModel,
    RoleBindingModel,
    TenantMembershipModel,
    TenantModel,
)
from serdial21.modules.audit.adapters.outbound.persistence.repositories import (
    SqlAlchemyAuditRepository,
)
from serdial21.modules.audit.application.services.audit import AuditRecord, AuditService
from serdial21.modules.audit.domain.entities import AuditOrigin


AUDIT_CONTEXT_KEY = 'serdial21.audit_context'


class MissingAuditContextError(RuntimeError):
    '''Falha fechada quando uma mutação crítica não possui autoria/correlação.'''


class AuditedEntityDeletionError(RuntimeError):
    '''Entidades iniciais usam transição de status, não exclusão física.'''


@dataclass(frozen=True, slots=True)
class AuditContext:
    correlation_id: UUID
    origin: AuditOrigin
    actor_id: UUID | None = None
    causation_id: UUID | None = None
    reason: str | None = None


@dataclass(frozen=True, slots=True)
class SubjectPolicy:
    subject_type: str
    action_prefix: str
    fields: tuple[str, ...]
    company_is_subject: bool = False
    version_field: str | None = None


SUBJECT_POLICIES: dict[type[object], SubjectPolicy] = {
    TenantModel: SubjectPolicy(
        subject_type='Tenant',
        action_prefix='tenant',
        fields=('status', 'timezone', 'currency_code'),
    ),
    CompanyModel: SubjectPolicy(
        subject_type='Company',
        action_prefix='company',
        fields=('status', 'timezone', 'currency_code', 'valid_from', 'valid_until'),
        company_is_subject=True,
    ),
    TenantMembershipModel: SubjectPolicy(
        subject_type='TenantMembership',
        action_prefix='membership',
        fields=(
            'user_id', 'status', 'relationship_type',
            'valid_from', 'valid_until', 'revision',
        ),
        version_field='revision',
    ),
    RoleBindingModel: SubjectPolicy(
        subject_type='RoleBinding',
        action_prefix='role_binding',
        fields=(
            'membership_id', 'role_id', 'company_id',
            'status', 'valid_from', 'valid_until',
        ),
    ),
}

_hooks_installed = False


@contextmanager
def audit_scope(
    session: Session,
    context: AuditContext,
) -> Generator[None, None, None]:
    if AUDIT_CONTEXT_KEY in session.info:
        raise RuntimeError('contexto de auditoria já está ativo nesta sessão')
    session.info[AUDIT_CONTEXT_KEY] = context
    try:
        yield
    finally:
        session.info.pop(AUDIT_CONTEXT_KEY, None)


def install_audit_hooks() -> None:
    global _hooks_installed
    if _hooks_installed:
        return
    event.listen(Session, 'before_flush', _audit_access_control_changes)
    _hooks_installed = True


def _audit_access_control_changes(
    session: Session,
    _: object,
    __: object,
) -> None:
    new_items = set(session.new)
    changed = [
        item
        for item in tuple(session.new) + tuple(session.dirty)
        if type(item) in SUBJECT_POLICIES
        and (item in new_items or session.is_modified(item, include_collections=False))
    ]
    deleted = [item for item in session.deleted if type(item) in SUBJECT_POLICIES]
    if deleted:
        raise AuditedEntityDeletionError(
            'exclusão física de entidade auditada não é permitida'
        )
    if not changed:
        return
    context = session.info.get(AUDIT_CONTEXT_KEY)
    if not isinstance(context, AuditContext):
        raise MissingAuditContextError('mutação crítica exige contexto de auditoria')

    service = AuditService(SqlAlchemyAuditRepository(session))
    for subject in changed:
        _record_subject(service, subject, subject in new_items, context)


def _record_subject(
    service: AuditService,
    subject: object,
    created: bool,
    context: AuditContext,
) -> None:
    if getattr(subject, 'id', None) is None:
        subject.id = uuid4()
    policy = SUBJECT_POLICIES[type(subject)]
    before, after = _states(subject, policy, created=created)
    tenant_id = subject.id if isinstance(subject, TenantModel) else subject.tenant_id
    company_id = (
        subject.id
        if policy.company_is_subject
        else getattr(subject, 'company_id', None)
    )
    version = (
        getattr(subject, policy.version_field)
        if policy.version_field is not None
        else None
    )
    action_suffix = 'created' if created else 'updated'
    service.record(
        AuditRecord(
            tenant_id=tenant_id,
            company_id=company_id,
            actor_id=context.actor_id,
            origin=context.origin,
            module='access_control',
            action=f'{policy.action_prefix}.{action_suffix}',
            subject_type=policy.subject_type,
            subject_id=subject.id,
            subject_version=version,
            before=before,
            after=after,
            reason=context.reason,
            correlation_id=context.correlation_id,
            causation_id=context.causation_id,
        )
    )


def _states(
    subject: object,
    policy: SubjectPolicy,
    *,
    created: bool,
) -> tuple[dict[str, Any] | None, dict[str, Any] | None]:
    if created:
        return None, {
            field: getattr(subject, field)
            for field in policy.fields
            if getattr(subject, field) is not None
        }

    state = inspect(subject)
    before: dict[str, Any] = {}
    after: dict[str, Any] = {}
    for field in policy.fields:
        history = state.attrs[field].history
        if not history.has_changes():
            continue
        before[field] = history.deleted[0] if history.deleted else None
        after[field] = history.added[0] if history.added else getattr(subject, field)
    return before or None, after or None
