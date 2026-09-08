from datetime import UTC, datetime
from uuid import uuid4

import pytest

from serdial21.modules.audit.application.services.audit import AuditService
from serdial21.modules.privacy.application.dsr_search import (
    DSRRecord, DSRSourceRegistry, GenerateDSRAccessReport, ManualSource,
    SearchDataSubjectData, SourceResult, SourceStatus, SubjectLocator,
)
from serdial21.modules.privacy.domain.entities import DataSubjectRequest, DsrStatus


class Repository:
    def __init__(self, request: DataSubjectRequest) -> None: self.request = request
    def get_dsr(self, tenant_id, request_id): return self.request if (tenant_id, request_id) == (self.request.tenant_id, self.request.id) else None

class AuditRepository:
    def __init__(self) -> None: self.events = []
    def append(self, event) -> None: self.events.append(event)
    def get(self, *_): return None
    def list_by_correlation(self, *_): return []

class Authorization:
    def __init__(self, granted: set[str]) -> None: self.granted = granted
    def require(self, request, **_):
        if request.permission.value not in self.granted: raise PermissionError('denied')

class Users:
    name = 'USERS'
    def __init__(self, tenant, record): self.tenant, self.record = tenant, record
    def search(self, locator, tenant):
        return SourceResult(self.name, SourceStatus.SEARCHED, (self.record,) if tenant == self.tenant else ())

def setup(status=DsrStatus.IN_REVIEW, permissions={'privacy.dsr.search', 'privacy.dsr.export'}):
    tenant, company, actor, correlation = uuid4(), uuid4(), uuid4(), uuid4()
    request = DataSubjectRequest(uuid4(), tenant, company, 'x' * 64, status, datetime.now(UTC), actor)
    record = DSRRecord('USERS', 'USER', str(uuid4()), 'user profile', 'NOT_RECORDED', 'PENDING_POLICY_APPROVAL', datetime.now(UTC))
    audit_repo = AuditRepository(); audit = AuditService(audit_repo)
    search = SearchDataSubjectData(Repository(request), DSRSourceRegistry((Users(tenant, record), ManualSource('DOCUMENT_STORAGE'))), Authorization(permissions), audit)
    return tenant, company, actor, correlation, request, audit_repo, search, Authorization(permissions), audit

def test_authorized_search_is_tenant_scoped_manual_and_audited():
    tenant, company, actor, correlation, request, events, search, _, _ = setup()
    result = search.execute(tenant, company, request.id, SubjectLocator('email', 'privacy-test-unique@example.invalid'), actor, correlation)
    assert len(result.records) == 1 and result.manifest.status == 'PARTIAL_WITH_MANUAL_SOURCES'
    assert result.manifest.sources_manual == 1 and events.events[-1].action == 'dsr.search_executed'
    assert 'privacy-test-unique@example.invalid' not in str(events.events[-1])

@pytest.mark.parametrize('status,permissions', [(DsrStatus.IDENTITY_PENDING, {'privacy.dsr.search'}), (DsrStatus.IN_REVIEW, set())])
def test_search_denies_pending_identity_or_permission(status, permissions):
    tenant, company, actor, correlation, request, _, search, _, _ = setup(status, permissions)
    with pytest.raises((PermissionError, ValueError)): search.execute(tenant, company, request.id, SubjectLocator('email', 'x@example.invalid'), actor, correlation)

def test_cross_tenant_search_returns_no_data_and_is_denied():
    tenant, company, actor, correlation, request, _, search, _, _ = setup()
    with pytest.raises(LookupError): search.execute(uuid4(), company, request.id, SubjectLocator('email', 'x@example.invalid'), actor, correlation)

def test_report_requires_both_permissions_is_memory_only_and_audited():
    tenant, company, actor, correlation, request, events, search, authorization, audit = setup()
    report = GenerateDSRAccessReport(search, authorization, audit).execute(tenant, company, request.id, SubjectLocator('email', 'privacy-test-unique@example.invalid'), actor, correlation)
    assert report.request_id == request.id and not hasattr(report, 'path')
    assert events.events[-1].action == 'dsr.report_generated'
    for permissions in ({'privacy.dsr.search'}, {'privacy.dsr.export'}):
        _, _, _, _, request, events, search, authorization, audit = setup(permissions=permissions)
        with pytest.raises(PermissionError): GenerateDSRAccessReport(search, authorization, audit).execute(tenant, company, request.id, SubjectLocator('email', 'x@example.invalid'), actor, correlation)
        assert not any(event.action == 'dsr.report_generated' for event in events.events)
