from datetime import UTC, datetime
from hashlib import sha256
from uuid import UUID, uuid4

from serdial21.modules.audit.application.services.audit import AuditRecord, AuditService
from serdial21.modules.audit.domain.entities import AuditOrigin
from serdial21.modules.access_control.application.services.authorization import AuthorizationRequest, AuthorizationService
from serdial21.modules.access_control.domain.permissions import PermissionCode
from serdial21.modules.privacy.application.ports.repository import PrivacyRepository
from serdial21.modules.privacy.domain.entities import (
    ApprovalStatus, DataSubjectRequest, DsrStatus, LegalHold, RetentionCandidate,
    RetentionDecision, RetentionEvaluation, RetentionPolicy, due, new_hold,
)


class PrivacyUnavailableError(LookupError): pass
class DestructiveRetentionDenied(PermissionError): pass


class AuthorizedPrivacyActions:
    '''Boundary privilegiado; mantém os serviços de decisão sem acoplamento de acesso.'''
    def __init__(self, authorization: AuthorizationService, retention: 'RetentionDecisionService',
                 holds: 'LegalHoldService', dsr: 'DataSubjectRequestService') -> None:
        self._authorization, self._retention, self._holds, self._dsr = authorization, retention, holds, dsr
    def evaluate(self, candidate, actor_id, correlation_id):
        self._require(candidate.tenant_id, candidate.company_id, actor_id, 'privacy.retention.evaluate')
        return self._retention.evaluate(candidate, actor_id=actor_id, correlation_id=correlation_id)
    def create_hold(self, tenant_id, company_id, resource_type, resource_id, reason, actor_id, correlation_id):
        self._require(tenant_id, company_id, actor_id, 'privacy.legal_hold.manage')
        return self._holds.create(tenant_id, company_id, resource_type, resource_id, reason, actor_id, correlation_id)
    def release_hold(self, tenant_id, company_id, hold_id, actor_id, correlation_id):
        self._require(tenant_id, company_id, actor_id, 'privacy.legal_hold.manage')
        return self._holds.release(tenant_id, hold_id, actor_id, correlation_id)
    def verify_dsr(self, tenant_id, company_id, request_id, actor_id, correlation_id):
        self._require(tenant_id, company_id, actor_id, 'privacy.dsr.manage')
        return self._dsr.verify_identity(tenant_id, request_id, actor_id, correlation_id)
    def _require(self, tenant_id, company_id, actor_id, permission):
        self._authorization.require(AuthorizationRequest(tenant_id, actor_id, PermissionCode(permission), company_id))


class RetentionDecisionService:
    def __init__(self, repository: PrivacyRepository, audit: AuditService, *, clock=None) -> None:
        self._repo, self._audit, self._clock = repository, audit, clock or (lambda: datetime.now(UTC))

    def evaluate(self, candidate: RetentionCandidate, *, actor_id: UUID, correlation_id: UUID) -> RetentionEvaluation:
        if candidate.resource_type == 'AuditEvent':
            return self._record(candidate, None, RetentionDecision.NOT_APPLICABLE, 'AUDIT_RETENTION_SPECIAL_HANDLING', actor_id, correlation_id)
        hold = self._repo.active_hold(candidate.tenant_id, candidate.company_id, candidate.resource_type, candidate.resource_id)
        if hold is not None:
            return self._record(candidate, None, RetentionDecision.LEGAL_HOLD, 'ACTIVE_LEGAL_HOLD', actor_id, correlation_id)
        policy = self._repo.policy(candidate.tenant_id, candidate.data_category)
        if policy is None or policy.approval_status is not ApprovalStatus.APPROVED:
            return self._record(candidate, policy, RetentionDecision.PENDING_POLICY_APPROVAL, 'POLICY_PENDING_HUMAN_APPROVAL', actor_id, correlation_id)
        decision = RetentionDecision.ELIGIBLE_FOR_RETENTION_ACTION if due(policy, candidate, self._clock()) else RetentionDecision.KEEP
        return self._record(candidate, policy, decision, 'RETENTION_PERIOD_' + ('ELAPSED' if decision is RetentionDecision.ELIGIBLE_FOR_RETENTION_ACTION else 'NOT_ELAPSED'), actor_id, correlation_id)

    def _record(self, candidate, policy, decision, reason, actor_id, correlation_id):
        result = RetentionEvaluation(candidate, policy.id if policy else None, decision, reason)
        self._audit.record(AuditRecord(candidate.tenant_id, candidate.company_id, actor_id, AuditOrigin.AUTOMATION,
            'privacy', 'retention.blocked_by_hold' if decision is RetentionDecision.LEGAL_HOLD else 'retention.evaluated',
            candidate.resource_type, candidate.resource_id, None, None,
            {'category': candidate.data_category, 'decision': decision.value, 'policy_id': str(policy.id) if policy else None}, None, correlation_id))
        return result


class RetentionRunner:
    def __init__(self, service: RetentionDecisionService, *, dry_run: bool = True) -> None:
        if not dry_run: raise DestructiveRetentionDenied('destructive retention is disabled by default')
        self._service = service
    def run(self, candidates, *, actor_id: UUID, correlation_id: UUID):
        return tuple(self._service.evaluate(item, actor_id=actor_id, correlation_id=correlation_id) for item in candidates)


class LegalHoldService:
    def __init__(self, repository: PrivacyRepository, audit: AuditService, *, clock=None) -> None:
        self._repo, self._audit, self._clock = repository, audit, clock or (lambda: datetime.now(UTC))
    def create(self, tenant_id, company_id, resource_type, resource_id, reason_reference, actor_id, correlation_id):
        hold = new_hold(tenant_id, company_id, resource_type, resource_id, reason_reference, actor_id, self._clock())
        self._repo.add_hold(hold); self._audit.record(AuditRecord(tenant_id, company_id, actor_id, AuditOrigin.HUMAN, 'privacy', 'legal_hold.created', 'LegalHold', hold.id, None, None, {'resource_type': resource_type, 'resource_id': str(resource_id) if resource_id else None}, None, correlation_id)); return hold
    def release(self, tenant_id, hold_id, actor_id, correlation_id):
        hold = self._repo.get_hold(tenant_id, hold_id)
        if hold is None: raise PrivacyUnavailableError()
        released = hold.release(actor_id, self._clock()); self._repo.save_hold(released)
        self._audit.record(AuditRecord(tenant_id, released.company_id, actor_id, AuditOrigin.HUMAN, 'privacy', 'legal_hold.released', 'LegalHold', hold_id, None, None, {'status': 'RELEASED'}, None, correlation_id)); return released


class DataSubjectRequestService:
    def __init__(self, repository: PrivacyRepository, audit: AuditService, *, clock=None) -> None:
        self._repo, self._audit, self._clock = repository, audit, clock or (lambda: datetime.now(UTC))
    def create(self, tenant_id, company_id, identifier: str, actor_id, correlation_id):
        if not identifier.strip(): raise ValueError('subject identifier is required')
        request = DataSubjectRequest(uuid4(), tenant_id, company_id, sha256(identifier.encode()).hexdigest(), DsrStatus.IDENTITY_PENDING, self._clock(), actor_id)
        self._repo.add_dsr(request); self._audit.record(AuditRecord(tenant_id, company_id, actor_id, AuditOrigin.HUMAN, 'privacy', 'dsr.received', 'DataSubjectRequest', request.id, None, None, {'status': request.status.value}, None, correlation_id)); return request
    def verify_identity(self, tenant_id, request_id, actor_id, correlation_id):
        request = self._get(tenant_id, request_id); updated = request.verify_identity(actor_id); self._repo.save_dsr(updated); self._audit.record(AuditRecord(tenant_id, updated.company_id, actor_id, AuditOrigin.HUMAN, 'privacy', 'dsr.identity_verified', 'DataSubjectRequest', request_id, None, None, {'status': updated.status.value}, None, correlation_id)); return updated
    def complete(self, tenant_id, request_id, actor_id, correlation_id):
        request = self._get(tenant_id, request_id); updated = request.complete(self._clock()); self._repo.save_dsr(updated); self._audit.record(AuditRecord(tenant_id, updated.company_id, actor_id, AuditOrigin.HUMAN, 'privacy', 'dsr.completed', 'DataSubjectRequest', request_id, None, None, {'status': updated.status.value}, None, correlation_id)); return updated
    def _get(self, tenant_id, request_id):
        request = self._repo.get_dsr(tenant_id, request_id)
        if request is None: raise PrivacyUnavailableError()
        return request
