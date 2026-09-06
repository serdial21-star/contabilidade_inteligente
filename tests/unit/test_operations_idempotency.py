from datetime import UTC, datetime
from uuid import UUID, uuid4

import pytest

from serdial21.modules.operations.application.services.idempotency import (
    CriticalCommand,
    IdempotentOperationService,
)
from serdial21.modules.operations.domain.entities import (
    CriticalOperation,
    IdempotencyConflictError,
    JobEffectState,
    JobRevalidationError,
    JobStatus,
    ProcessingJob,
    revalidate_job,
)


NOW = datetime(2026, 9, 6, 12, 0, tzinfo=UTC)


class Repository:
    def __init__(self, *, fail_commit: bool = False) -> None:
        self.receipts: dict[tuple[UUID, UUID, str, str], object] = {}
        self.events: list[object] = []
        self.outbox: list[object] = []
        self.effects: list[UUID] = []
        self.fail_commit = fail_commit

    def find_inbox_receipt(self, tenant_id: UUID, company_id: UUID, consumer: str,
                           idempotency_key: str) -> object | None:
        return self.receipts.get((tenant_id, company_id, consumer, idempotency_key))

    def commit_effect_with_messages(self, *, result_id: UUID, event: object,
                                    outbox: object, receipt: object) -> None:
        if self.fail_commit:
            raise RuntimeError('simulated transaction failure')
        self.effects.append(result_id)
        self.events.append(event)
        self.outbox.append(outbox)
        self.receipts[(receipt.tenant_id, receipt.company_id, receipt.consumer, receipt.idempotency_key)] = receipt


def command(operation: CriticalOperation, *, payload_hash: str = 'hash') -> CriticalCommand:
    return CriticalCommand(uuid4(), uuid4(), 'worker', 'key', payload_hash, operation,
                           'Subject', uuid4())


@pytest.mark.parametrize('operation', tuple(CriticalOperation))
def test_retry_of_every_critical_operation_returns_same_effect(operation: CriticalOperation) -> None:
    repository = Repository()
    service = IdempotentOperationService(repository, clock=lambda: NOW)
    request = command(operation)
    calls = 0

    def effect() -> UUID:
        nonlocal calls
        calls += 1
        return uuid4()

    first = service.execute(request, effect)
    retry = service.execute(request, effect)
    assert first.result_id == retry.result_id
    assert retry.reused is True
    assert calls == 1
    assert len(repository.events) == len(repository.outbox) == len(repository.effects) == 1


def test_same_key_with_different_hash_is_conflict() -> None:
    repository = Repository()
    service = IdempotentOperationService(repository, clock=lambda: NOW)
    original = command(CriticalOperation.IMPORT)
    service.execute(original, uuid4)
    changed = CriticalCommand(original.tenant_id, original.company_id, original.consumer,
                              original.idempotency_key, 'changed', original.operation,
                              original.subject_type, original.correlation_id)
    with pytest.raises(IdempotencyConflictError, match='different content'):
        service.execute(changed, uuid4)


def test_failed_commit_persists_neither_effect_event_outbox_nor_inbox() -> None:
    repository = Repository(fail_commit=True)
    service = IdempotentOperationService(repository, clock=lambda: NOW)
    with pytest.raises(RuntimeError, match='transaction failure'):
        service.execute(command(CriticalOperation.JOURNAL), uuid4)
    assert not repository.effects and not repository.events and not repository.outbox and not repository.receipts


def test_job_revalidates_tenant_permission_version_lock_and_status_before_effect() -> None:
    tenant_id, company_id = uuid4(), uuid4()
    job = ProcessingJob(uuid4(), tenant_id, company_id, CriticalOperation.EXPORT, uuid4(),
                        'export.execute', 3, 'READY', JobStatus.PENDING, 'job-key')
    valid = JobEffectState(tenant_id, company_id, 3, 'READY', True, True)
    revalidate_job(job, valid)
    for state in (
        JobEffectState(uuid4(), company_id, 3, 'READY', True, True),
        JobEffectState(tenant_id, company_id, 3, 'READY', False, True),
        JobEffectState(tenant_id, company_id, 2, 'READY', True, True),
        JobEffectState(tenant_id, company_id, 3, 'READY', True, False),
        JobEffectState(tenant_id, company_id, 3, 'CHANGED', True, True),
    ):
        with pytest.raises(JobRevalidationError):
            revalidate_job(job, state)
