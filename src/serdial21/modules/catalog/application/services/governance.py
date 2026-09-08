'''DRAFT -> REVIEW -> PUBLISHED com segregação e auditoria.'''

from collections.abc import Callable
from datetime import UTC, datetime
from uuid import UUID

from serdial21.modules.access_control.application.services.authorization import (
    AuthorizationRequest, AuthorizationService,
)
from serdial21.modules.access_control.domain.permissions import PermissionCode
from serdial21.modules.audit.application.services.audit import AuditRecord, AuditService
from serdial21.modules.audit.domain.entities import AuditOrigin
from serdial21.modules.catalog.application.ports.repository import CatalogRepository
from serdial21.modules.catalog.domain.entities import (
    CatalogConflictError, CatalogSpec, CatalogUnavailableError, CatalogVersion,
)
from serdial21.modules.catalog.snapshot import compile_snapshot, snapshot_hash, transition_snapshot


class CatalogGovernanceService:
    def __init__(
        self, repository: CatalogRepository, authorization: AuthorizationService,
        audit: AuditService, *, clock: Callable[[], datetime] | None = None,
    ) -> None:
        self._repository = repository
        self._authorization = authorization
        self._audit = audit
        self._clock = clock or (lambda: datetime.now(UTC))

    def create_draft(
        self, tenant_id: UUID, company_id: UUID, actor_id: UUID,
        spec: CatalogSpec, *, correlation_id: UUID, reason: str,
    ) -> CatalogVersion:
        self._require(tenant_id, company_id, actor_id, 'catalog.manage')
        now = self._now()
        content = compile_snapshot(spec, 1)
        version = self._repository.add_draft(
            tenant_id, company_id, spec.name, 1, content, snapshot_hash(content),
            actor_id, now, spec.valid_from, spec.valid_to,
        )
        self._record(version, actor_id, 'catalog.draft.created', correlation_id, reason)
        return version

    def create_next_draft(
        self, tenant_id: UUID, company_id: UUID, actor_id: UUID,
        published_version_id: UUID, spec: CatalogSpec, *,
        correlation_id: UUID, reason: str,
    ) -> CatalogVersion:
        self._require(tenant_id, company_id, actor_id, 'catalog.manage')
        previous = self._get(tenant_id, company_id, published_version_id)
        if previous.status != 'PUBLISHED':
            raise CatalogConflictError('nova versão exige catálogo publicado')
        content = compile_snapshot(
            spec, previous.version_no + 1,
            previous=self._repository.content(previous.id),
        )
        now = self._now()
        version = self._repository.add_draft(
            tenant_id, company_id, spec.name, previous.version_no + 1,
            content, snapshot_hash(content), actor_id, now,
            spec.valid_from, spec.valid_to, catalog_id=previous.catalog_id,
            supersedes_version_id=previous.id,
        )
        self._record(version, actor_id, 'catalog.version.created', correlation_id, reason)
        return version

    def submit_review(
        self, tenant_id: UUID, company_id: UUID, actor_id: UUID,
        version_id: UUID, *, correlation_id: UUID, reason: str,
    ) -> CatalogVersion:
        self._require(tenant_id, company_id, actor_id, 'catalog.manage')
        current = self._get(tenant_id, company_id, version_id)
        if current.status != 'DRAFT':
            raise CatalogConflictError('somente DRAFT pode seguir para REVIEW')
        content = transition_snapshot(self._repository.content(version_id), 'DRAFT', 'REVIEW')
        version = self._repository.transition(
            version_id, 'DRAFT', 'REVIEW', content, snapshot_hash(content), actor_id, self._now(),
        )
        self._record(version, actor_id, 'catalog.review.requested', correlation_id, reason)
        return version

    def publish(
        self, tenant_id: UUID, company_id: UUID, actor_id: UUID,
        version_id: UUID, *, correlation_id: UUID, reason: str,
    ) -> CatalogVersion:
        self._require(tenant_id, company_id, actor_id, 'catalog.review')
        current = self._get(tenant_id, company_id, version_id)
        if current.status != 'REVIEW':
            raise CatalogConflictError('somente REVIEW pode ser publicada')
        if current.created_by == actor_id:
            raise PermissionError('segregação de função do catálogo')
        content = transition_snapshot(self._repository.content(version_id), 'REVIEW', 'PUBLISHED')
        version = self._repository.transition(
            version_id, 'REVIEW', 'PUBLISHED', content, snapshot_hash(content),
            actor_id, self._now(),
        )
        self._record(version, actor_id, 'catalog.published', correlation_id, reason)
        return version

    def _get(self, tenant_id: UUID, company_id: UUID, version_id: UUID) -> CatalogVersion:
        version = self._repository.get_for_update(tenant_id, company_id, version_id)
        if version is None:
            raise CatalogUnavailableError()
        return version

    def _require(
        self, tenant_id: UUID, company_id: UUID, actor_id: UUID, permission: str,
    ) -> None:
        self._authorization.require(AuthorizationRequest(
            tenant_id, actor_id, PermissionCode(permission), company_id,
        ), at=self._now())

    def _record(
        self, version: CatalogVersion, actor_id: UUID, action: str,
        correlation_id: UUID, reason: str,
    ) -> None:
        self._audit.record(AuditRecord(
            tenant_id=version.tenant_id, company_id=version.company_id,
            actor_id=actor_id, origin=AuditOrigin.HUMAN, module='catalog',
            action=action, subject_type='ProductionCatalogVersion',
            subject_id=version.id, subject_version=version.version_no,
            before=None, after={
                'status': version.status,
                'version_no': version.version_no,
                'content_hash': version.content_hash,
            }, reason=reason, correlation_id=correlation_id,
        ))

    def _now(self) -> datetime:
        value = self._clock()
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError('clock do catálogo exige timezone')
        return value.astimezone(UTC)
