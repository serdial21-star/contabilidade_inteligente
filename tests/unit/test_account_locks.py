from datetime import UTC, date, datetime
from uuid import UUID, uuid4

import pytest

from serdial21.modules.access_control.application.services.authorization import AuthorizedContext
from serdial21.modules.access_control.domain.permissions import PermissionCode
from serdial21.modules.audit.application.services.audit import AuditService
from serdial21.modules.audit.domain.entities import AuditEvent
from serdial21.modules.locks.application.services.locks import AccountLockService
from serdial21.modules.locks.domain.entities import (
    AccountLockedError,
    EffectChannel,
    EffectContext,
    EffectOperation,
    LockScope,
    create_lock,
    validate_effect,
)


NOW = datetime(2026, 9, 6, 12, 0, tzinfo=UTC)


class AuditRepository:
    def __init__(self) -> None:
        self.events: list[AuditEvent] = []

    def append(self, event: AuditEvent) -> None:
        self.events.append(event)

    def get(self, tenant_id: UUID, event_id: UUID) -> AuditEvent | None:
        return None

    def list_by_correlation(self, tenant_id: UUID, correlation_id: UUID) -> list[AuditEvent]:
        return []


def setup() -> tuple[object, EffectContext]:
    tenant_id, company_id, account_id = uuid4(), uuid4(), uuid4()
    lock = create_lock(
        tenant_id=tenant_id, company_id=company_id, scope=LockScope.ACCOUNT,
        operations=(EffectOperation.ALTER,), reason='reconciled period', account_id=account_id,
    )
    return lock, EffectContext(
        tenant_id, company_id, account_id, (), 'ACCOUNTING', date(2026, 9, 6),
        EffectOperation.ALTER, EffectChannel.USER,
    )


@pytest.mark.parametrize('channel', tuple(EffectChannel))
def test_lock_is_revalidated_at_effect_for_every_channel(channel: EffectChannel) -> None:
    lock, context = setup()

    with pytest.raises(AccountLockedError):
        validate_effect((lock,), EffectContext(
            context.tenant_id, context.company_id, context.account_id, context.group_ids,
            context.module, context.accounting_date, context.operation, channel,
        ))


@pytest.mark.parametrize('scope,kwargs', (
    (LockScope.GROUP, {'group_id': uuid4()}),
    (LockScope.MODULE, {'module': 'ACCOUNTING'}),
    (LockScope.COMPETENCE, {'competence': date(2026, 9, 1)}),
    (LockScope.EXERCISE, {'exercise': 2026}),
))
def test_all_supported_lock_scopes_block_the_effect(
    scope: LockScope,
    kwargs: dict[str, object],
) -> None:
    _, context = setup()
    lock = create_lock(
        tenant_id=context.tenant_id, company_id=context.company_id, scope=scope,
        operations=(EffectOperation.ALTER,), reason='control', **kwargs,
    )
    groups = (lock.group_id,) if lock.group_id else ()

    with pytest.raises(AccountLockedError):
        validate_effect((lock,), EffectContext(
            context.tenant_id, context.company_id, context.account_id, groups,
            context.module, context.accounting_date, context.operation, EffectChannel.API,
        ))


def test_cross_tenant_lock_does_not_block_and_release_requires_permission_and_audit() -> None:
    lock, context = setup()
    foreign = create_lock(
        tenant_id=uuid4(), company_id=uuid4(), scope=LockScope.ACCOUNT,
        operations=(EffectOperation.ALTER,), reason='foreign', account_id=context.account_id,
    )
    assert validate_effect((foreign,), context).reconciliation_requires_review is False
    repository = AuditRepository()
    service = AccountLockService(AuditService(repository, clock=lambda: NOW))
    denied = AuthorizedContext(
        context.tenant_id, uuid4(), uuid4(), context.company_id,
        PermissionCode('journal.approve'), NOW,
    )
    with pytest.raises(PermissionError):
        service.release(lock, authorization=denied, reason='correction', correlation_id=uuid4(), released_at=NOW)
    allowed = AuthorizedContext(
        context.tenant_id, uuid4(), uuid4(), context.company_id,
        PermissionCode('lock.manage'), NOW,
    )
    released = service.release(lock, authorization=allowed, reason='correction', correlation_id=uuid4(), released_at=NOW)
    assert released.lock.status.value == 'RELEASED'
    assert released.audit_event.action == 'account_lock.released'
    assert released.jobs_resumed is False


def test_effect_after_release_requires_review_without_resuming_jobs() -> None:
    lock, context = setup()
    allowed = AuthorizedContext(
        context.tenant_id, uuid4(), uuid4(), context.company_id,
        PermissionCode('lock.manage'), NOW,
    )
    released = AccountLockService(AuditService(AuditRepository(), clock=lambda: NOW)).release(
        lock, authorization=allowed, reason='fix', correlation_id=uuid4(), released_at=NOW,
    ).lock

    validation = validate_effect((released,), context)

    assert validation.reconciliation_requires_review is True
    assert validation.jobs_resumed is False
