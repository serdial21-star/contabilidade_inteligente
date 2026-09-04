from dataclasses import replace
from datetime import UTC, datetime
from uuid import UUID, uuid4

import pytest

from serdial21.modules.audit.application.services.audit import (
    AuditRecord,
    AuditService,
    SensitiveAuditDataError,
)
from serdial21.modules.audit.domain.entities import AuditEvent, AuditOrigin


NOW = datetime(2026, 9, 4, 12, 0, tzinfo=UTC)


class FakeAuditRepository:
    def __init__(self) -> None:
        self.events: list[AuditEvent] = []

    def append(self, audit_event: AuditEvent) -> None:
        self.events.append(audit_event)

    def get(self, tenant_id: UUID, event_id: UUID) -> AuditEvent | None:
        return next(
            (
                item
                for item in self.events
                if item.tenant_id == tenant_id and item.id == event_id
            ),
            None,
        )

    def list_by_correlation(
        self,
        tenant_id: UUID,
        correlation_id: UUID,
    ) -> list[AuditEvent]:
        return [
            item
            for item in self.events
            if item.tenant_id == tenant_id
            and item.correlation_id == correlation_id
        ]


def audit_record(**changes: object) -> AuditRecord:
    values: dict[str, object] = {
        'tenant_id': uuid4(),
        'company_id': None,
        'actor_id': uuid4(),
        'origin': AuditOrigin.HUMAN,
        'module': 'access_control',
        'action': 'tenant.updated',
        'subject_type': 'Tenant',
        'subject_id': uuid4(),
        'subject_version': None,
        'before': {'status': 'pending'},
        'after': {'status': 'active'},
        'reason': 'activation approved',
        'correlation_id': uuid4(),
        'causation_id': None,
    }
    values.update(changes)
    return AuditRecord(**values)


def test_record_creates_correlated_event_with_valid_integrity() -> None:
    repository = FakeAuditRepository()
    event_id = uuid4()
    record = audit_record()
    service = AuditService(
        repository,
        id_factory=lambda: event_id,
        clock=lambda: NOW,
    )

    event = service.record(record)

    assert event.id == event_id
    assert event.correlation_id == record.correlation_id
    assert event.occurred_at == NOW
    assert repository.events == [event]
    assert service.verify_integrity(event) is True
    assert service.verify_integrity(replace(event, action='tenant.closed')) is False


@pytest.mark.parametrize(
    'state',
    (
        {'password': 'not-allowed'},
        {'api_token': 'not-allowed'},
        {'document_xml': '<NFe>raw</NFe>'},
        {'content': '<?xml version=1.0?>'},
    ),
)
def test_sensitive_or_raw_content_is_rejected(
    state: dict[str, object],
) -> None:
    service = AuditService(FakeAuditRepository(), clock=lambda: NOW)

    with pytest.raises(SensitiveAuditDataError):
        service.record(audit_record(after=state))
