from dataclasses import dataclass
from datetime import UTC, datetime
from uuid import UUID, uuid4

from serdial21.modules.audit.application.services.audit import AuditRecord, AuditService
from serdial21.modules.audit.domain.entities import AuditEvent, AuditOrigin
from serdial21.modules.operations.application.services.traceability import (
    DecisionLineRoot, DecisionLineService,
)


NOW = datetime(2026, 9, 15, 12, 0, tzinfo=UTC)


class AuditRepository:
    def __init__(self) -> None:
        self.events: list[AuditEvent] = []

    def append(self, event: AuditEvent) -> None:
        self.events.append(event)

    def get(self, tenant_id: UUID, event_id: UUID) -> AuditEvent | None:
        return next((event for event in self.events if event.id == event_id), None)

    def list_by_correlation(self, tenant_id: UUID, correlation_id: UUID) -> list[AuditEvent]:
        return [event for event in self.events if event.correlation_id == correlation_id]


class Authorization:
    def __init__(self) -> None:
        self.permissions: list[str] = []

    def require(self, request: object) -> None:
        self.permissions.append(request.permission.value)


@dataclass
class Document:
    id: UUID
    artifact_id: UUID
    filename: str = 'safe.xml'
    processing_status: str = 'PENDING_RULE'


class Repository:
    def __init__(self, document: Document, events: tuple[AuditEvent, ...], correlation: UUID, actor: UUID) -> None:
        self.document = document
        self.events = events
        self.correlation = correlation
        self.actor = actor

    def get_document(self, tenant_id: UUID, company_id: UUID, document_id: UUID) -> Document | None:
        return self.document if document_id == self.document.id else None

    def linked_fiscal_document_id(self, tenant_id: UUID, company_id: UUID, artifact_id: UUID) -> UUID | None:
        return None

    def get_journey_by_fiscal_document(self, tenant_id: UUID, company_id: UUID, fiscal_document_id: UUID) -> None:
        return None

    def find_trace_correlation_ids(self, tenant_id: UUID, company_id: UUID, references: tuple[tuple[str, UUID], ...], *, limit: int) -> tuple[UUID, ...]:
        return (self.correlation,)

    def list_trace_audit_events(self, tenant_id: UUID, company_id: UUID, correlation_ids: tuple[UUID, ...], *, limit: int) -> tuple[AuditEvent, ...]:
        return self.events[:limit]

    def actor_display_names(self, tenant_id: UUID, actor_ids: tuple[UUID, ...]) -> dict[UUID, str]:
        return {self.actor: '<script>alert(1)</script>'}


def _event(service: AuditService, tenant: UUID, company: UUID, actor: UUID, correlation: UUID, action: str, status: str) -> AuditEvent:
    return service.record(AuditRecord(
        tenant, company, actor, AuditOrigin.HUMAN, 'workflow', action,
        'Journey', uuid4(), 1, None, {'status': status}, None, correlation,
    ))


def test_no_rule_trace_is_stable_minimized_and_stops_without_proposal() -> None:
    tenant, company, actor, correlation = uuid4(), uuid4(), uuid4(), uuid4()
    audit_repository = AuditRepository()
    ids = iter((UUID(int=2), UUID(int=1)))
    audit = AuditService(audit_repository, id_factory=lambda: next(ids), clock=lambda: NOW)
    events = (
        _event(audit, tenant, company, actor, correlation, 'journey.pending_rule', 'PENDING_RULE'),
        _event(audit, tenant, company, actor, correlation, 'artifact_receipt.created', 'ACCEPTED'),
    )
    authorization = Authorization()
    document = Document(uuid4(), uuid4())
    line = DecisionLineService(
        Repository(document, events, correlation, actor), authorization, audit,
    ).get(tenant, company, actor, DecisionLineRoot.DOCUMENT, document.id, limit=20)

    assert authorization.permissions == ['company.read', 'audit.read']
    assert [event.sequence for event in line.events] == [1, 2]
    assert [event.category for event in line.events] == ['RECEIPT', 'EXCEPTION']
    assert not any(event.category == 'PROPOSAL' for event in line.events)
    assert line.events[0].actor_display_name == '<script>alert(1)</script>'
    assert all(event.evidence_kind == 'AUDIT_EVENT' for event in line.events)
    assert all(event.integrity_valid for event in line.events)


def test_rejection_is_a_professional_decision_without_raw_reason() -> None:
    tenant, company, actor, correlation = uuid4(), uuid4(), uuid4(), uuid4()
    audit_repository = AuditRepository()
    audit = AuditService(audit_repository, clock=lambda: NOW)
    event = _event(
        audit, tenant, company, actor, correlation,
        'approval_decision.recorded', 'REJECTED',
    )
    projected = DecisionLineService(
        Repository(Document(uuid4(), uuid4()), (event,), correlation, actor),
        Authorization(), audit,
    )._project(event, {actor: 'Contadora Exemplo'})

    assert projected.category == 'REJECTION'
    assert projected.actor_kind == 'PROFESSIONAL_ACTION'
    assert projected.actor_display_name == 'Contadora Exemplo'
    assert 'reason' not in projected.description.lower()


def test_unknown_historical_event_uses_controlled_fallback_without_raw_action() -> None:
    tenant, company, actor, correlation = uuid4(), uuid4(), uuid4(), uuid4()
    audit_repository = AuditRepository()
    audit = AuditService(audit_repository, clock=lambda: NOW)
    event = _event(
        audit, tenant, company, actor, correlation,
        'legacy.raw_action_with_secret_name', 'LEGACY',
    )

    projected = DecisionLineService(
        Repository(Document(uuid4(), uuid4()), (event,), correlation, actor),
        Authorization(), audit,
    )._project(event, {actor: 'Contadora Exemplo'})

    assert projected.category == 'EXCEPTION'
    assert projected.actor_kind == 'SYSTEM_GOVERNANCE'
    assert projected.title == 'Registro operacional correlacionado'
    assert 'legacy.raw_action_with_secret_name' not in projected.description
