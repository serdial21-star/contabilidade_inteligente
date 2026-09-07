from collections.abc import Generator
from datetime import UTC, datetime
from pathlib import Path
from uuid import UUID, uuid4

import pytest
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from serdial21.bootstrap.audit import AuditContext, audit_scope
from serdial21.bootstrap.database import Base, create_database_engine, create_session_factory
from serdial21.bootstrap.model_registry import load_models
from serdial21.bootstrap.settings import AppSettings
from serdial21.modules.access_control.adapters.outbound.persistence.models import (
    CompanyModel,
    TenantModel,
)
from serdial21.modules.audit.adapters.outbound.persistence.repositories import (
    SqlAlchemyAuditRepository,
)
from serdial21.modules.audit.application.services.audit import AuditService
from serdial21.modules.audit.domain.entities import AuditOrigin
from serdial21.modules.intake_documents.adapters.outbound.persistence.models import (
    ArtifactReceiptModel,
    EvidenceArtifactModel,
    ImmutableDocumentError,
    ImportBatchModel,
    ImportItemModel,
    LineageEdgeModel,
    ValidationIssueModel,
)
from serdial21.modules.intake_documents.adapters.outbound.persistence.repositories import (
    SqlAlchemyIntakeRepository,
)
from serdial21.modules.intake_documents.adapters.outbound.storage.local import (
    LocalObjectStorage,
)
from serdial21.modules.intake_documents.application.services.intake import (
    DocumentIntakeService,
    IntakeContext,
    IntakeResourceUnavailableError,
    InvalidLineageError,
    LineageRequest,
    StartBatchRequest,
    TransformationRequest,
    UploadRequest,
    UploadTooLargeError,
    ValidationIssueRequest,
)


NOW = datetime(2026, 9, 4, 15, 0, tzinfo=UTC)


class AllowDocumentAuthorization:
    def require_company_manage(
        self,
        tenant_id: UUID,
        company_id: UUID,
        actor_id: UUID | None,
        *,
        at: datetime,
    ) -> None:
        assert tenant_id
        assert company_id
        assert actor_id
        assert at == NOW


class DenyDocumentAuthorization:
    def require_company_manage(
        self,
        tenant_id: UUID,
        company_id: UUID,
        actor_id: UUID | None,
        *,
        at: datetime,
    ) -> None:
        raise PermissionError('access denied')


@pytest.fixture
def database_session() -> Generator[Session, None, None]:
    settings = AppSettings(
        _env_file=None,
        environment='test',
        database_url='sqlite+pysqlite:///:memory:',
    )
    engine = create_database_engine(settings)
    load_models()
    Base.metadata.create_all(engine)
    session = create_session_factory(engine)()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(engine)
        engine.dispose()


def seed_company(session: Session, tenant_id: UUID, company_id: UUID) -> None:
    audit_context = AuditContext(
        correlation_id=uuid4(),
        origin=AuditOrigin.API,
        actor_id=uuid4(),
        reason='document intake test setup',
    )
    with audit_scope(session, audit_context):
        session.add(TenantModel(
            id=tenant_id,
            name=f'Tenant {tenant_id}',
            timezone='America/Sao_Paulo',
            currency_code='BRL',
            status='active',
        ))
        session.flush()
        session.add(CompanyModel(
            id=company_id,
            tenant_id=tenant_id,
            legal_name=f'Company {company_id}',
            tax_identifier=company_id.hex[:14],
            timezone='America/Sao_Paulo',
            currency_code='BRL',
            status='active',
            valid_from=NOW,
        ))
        session.commit()


def service_for(session: Session, root: Path) -> DocumentIntakeService:
    return DocumentIntakeService(
        SqlAlchemyIntakeRepository(session),
        LocalObjectStorage(root),
        AuditService(SqlAlchemyAuditRepository(session), clock=lambda: NOW),
        AllowDocumentAuthorization(),
        clock=lambda: NOW,
    )


def intake_context(tenant_id: UUID, company_id: UUID) -> IntakeContext:
    return IntakeContext(
        tenant_id=tenant_id,
        company_id=company_id,
        actor_id=uuid4(),
        origin=AuditOrigin.HUMAN,
        correlation_id=uuid4(),
    )


def upload_request(batch_id: UUID, filename: str = 'evidence.bin') -> UploadRequest:
    return UploadRequest(
        batch_id=batch_id,
        content=b'same immutable evidence',
        original_filename=filename,
        media_type='application/octet-stream',
        classification='ACCOUNTING_EVIDENCE',
        channel='UPLOAD',
    )


def start_batch(
    service: DocumentIntakeService,
    context: IntakeContext,
    key: str = 'batch-1',
):
    return service.start_batch(
        context,
        StartBatchRequest(source='MANUAL_UPLOAD', idempotency_key=key),
    )


def test_upload_hash_deduplication_and_repeated_receipt(
    database_session: Session,
    tmp_path: Path,
) -> None:
    tenant_id, company_id = uuid4(), uuid4()
    seed_company(database_session, tenant_id, company_id)
    service = service_for(database_session, tmp_path)
    context = intake_context(tenant_id, company_id)
    batch = start_batch(service, context)

    first = service.upload(context, upload_request(batch.id, 'first.bin'))
    second = service.upload(context, upload_request(batch.id, 'second.bin'))
    database_session.commit()

    assert first.content_hash == second.content_hash
    assert first.artifact_id == second.artifact_id
    assert first.duplicate is False
    assert second.duplicate is True
    assert database_session.scalar(
        select(func.count()).select_from(EvidenceArtifactModel)
    ) == 1
    assert database_session.scalar(
        select(func.count()).select_from(ArtifactReceiptModel)
    ) == 2
    assert database_session.scalar(
        select(func.count()).select_from(ImportItemModel)
    ) == 2
    persisted_batch = database_session.get(ImportBatchModel, batch.id)
    assert persisted_batch is not None
    assert (persisted_batch.total_items, persisted_batch.duplicate_items) == (2, 1)
    assert LocalObjectStorage(tmp_path).read(first.storage_key) == b'same immutable evidence'


def test_authorization_is_required_before_batch_or_storage_write(
    database_session: Session,
    tmp_path: Path,
) -> None:
    tenant_id, company_id = uuid4(), uuid4()
    seed_company(database_session, tenant_id, company_id)
    service = DocumentIntakeService(
        SqlAlchemyIntakeRepository(database_session),
        LocalObjectStorage(tmp_path),
        AuditService(SqlAlchemyAuditRepository(database_session), clock=lambda: NOW),
        DenyDocumentAuthorization(),
        clock=lambda: NOW,
    )

    with pytest.raises(PermissionError, match='access denied'):
        start_batch(service, intake_context(tenant_id, company_id))

    assert list(tmp_path.rglob('*')) == []
    assert database_session.scalar(
        select(func.count()).select_from(ImportBatchModel)
    ) == 0


def test_invalid_batch_cannot_create_orphaned_storage_object(
    database_session: Session,
    tmp_path: Path,
) -> None:
    tenant_id, company_id = uuid4(), uuid4()
    seed_company(database_session, tenant_id, company_id)
    service = service_for(database_session, tmp_path)
    context = intake_context(tenant_id, company_id)

    with pytest.raises(IntakeResourceUnavailableError, match='resource unavailable'):
        service.upload(context, upload_request(uuid4()))

    assert list(tmp_path.rglob('*')) == []
    assert database_session.scalar(
        select(func.count()).select_from(EvidenceArtifactModel)
    ) == 0


def test_upload_limit_rejects_content_before_storage_write(
    database_session: Session,
    tmp_path: Path,
) -> None:
    tenant_id, company_id = uuid4(), uuid4()
    seed_company(database_session, tenant_id, company_id)
    service = DocumentIntakeService(
        SqlAlchemyIntakeRepository(database_session),
        LocalObjectStorage(tmp_path),
        AuditService(SqlAlchemyAuditRepository(database_session), clock=lambda: NOW),
        AllowDocumentAuthorization(),
        max_upload_bytes=4,
        clock=lambda: NOW,
    )
    context = intake_context(tenant_id, company_id)
    batch = start_batch(service, context)
    request = upload_request(batch.id)
    oversized = UploadRequest(
        batch_id=request.batch_id,
        content=b'12345',
        original_filename=request.original_filename,
        media_type=request.media_type,
        classification=request.classification,
        channel=request.channel,
    )

    with pytest.raises(UploadTooLargeError, match='limite de upload'):
        service.upload(context, oversized)

    assert list(tmp_path.rglob('*')) == []
    assert database_session.scalar(
        select(func.count()).select_from(EvidenceArtifactModel)
    ) == 0


def test_artifact_is_tenant_isolated_and_company_receipt_is_required(
    database_session: Session,
    tmp_path: Path,
) -> None:
    tenant_a, company_a = uuid4(), uuid4()
    tenant_b, company_b = uuid4(), uuid4()
    seed_company(database_session, tenant_a, company_a)
    seed_company(database_session, tenant_b, company_b)
    service = service_for(database_session, tmp_path)
    context_a = intake_context(tenant_a, company_a)
    context_b = intake_context(tenant_b, company_b)
    artifact_a = service.upload(context_a, upload_request(start_batch(service, context_a).id))
    artifact_b = service.upload(
        context_b,
        upload_request(start_batch(service, context_b, 'batch-b').id),
    )
    database_session.commit()

    repository = SqlAlchemyIntakeRepository(database_session)
    assert artifact_a.artifact_id != artifact_b.artifact_id
    assert repository.get_artifact(tenant_b, artifact_a.artifact_id) is None
    with pytest.raises(IntakeResourceUnavailableError):
        service.record_transformation(context_b, TransformationRequest(
            artifact_id=artifact_a.artifact_id,
            previous_run_id=None,
            parser_name='generic',
            parser_version='1',
            schema_version=None,
            output_hash=None,
            status='STARTED',
        ))


def test_artifact_cannot_be_changed_or_deleted(
    database_session: Session,
    tmp_path: Path,
) -> None:
    tenant_id, company_id = uuid4(), uuid4()
    seed_company(database_session, tenant_id, company_id)
    service = service_for(database_session, tmp_path)
    context = intake_context(tenant_id, company_id)
    result = service.upload(context, upload_request(start_batch(service, context).id))
    database_session.commit()

    artifact = database_session.get(EvidenceArtifactModel, result.artifact_id)
    assert artifact is not None
    artifact.classification = 'CHANGED'
    with pytest.raises(ImmutableDocumentError):
        database_session.commit()
    database_session.rollback()

    artifact = database_session.get(EvidenceArtifactModel, result.artifact_id)
    assert artifact is not None
    database_session.delete(artifact)
    with pytest.raises(ImmutableDocumentError):
        database_session.commit()
    database_session.rollback()


def test_transformation_validation_and_lineage_are_traceable(
    database_session: Session,
    tmp_path: Path,
) -> None:
    tenant_id, company_id = uuid4(), uuid4()
    seed_company(database_session, tenant_id, company_id)
    service = service_for(database_session, tmp_path)
    context = intake_context(tenant_id, company_id)
    artifact = service.upload(context, upload_request(start_batch(service, context).id))
    run = service.record_transformation(context, TransformationRequest(
        artifact_id=artifact.artifact_id,
        previous_run_id=None,
        parser_name='generic-validator',
        parser_version='1.0.0',
        schema_version='generic-v1',
        output_hash='a' * 64,
        status='COMPLETED',
    ))
    issue = service.add_validation_issue(context, ValidationIssueRequest(
        transformation_run_id=run.id,
        code='MISSING_REQUIRED_FIELD',
        severity='ERROR',
        field_path='header.identifier',
        rule_reference='generic-v1',
        message='Required field is absent',
    ))
    database_session.commit()

    edges = SqlAlchemyIntakeRepository(database_session).list_lineage_from(
        tenant_id,
        company_id,
        'EvidenceArtifact',
        artifact.artifact_id,
    )
    assert len(edges) == 1
    assert edges[0].target_id == run.id
    assert database_session.get(ValidationIssueModel, issue.id) is not None
    assert database_session.scalar(
        select(func.count()).select_from(LineageEdgeModel)
    ) == 1

    with pytest.raises(InvalidLineageError):
        service.add_lineage(context, LineageRequest(
            source_type='TransformationRun',
            source_id=run.id,
            source_version=None,
            target_type='EvidenceArtifact',
            target_id=artifact.artifact_id,
            target_version=None,
            transformation_run_id=run.id,
            relation='INVALID_REVERSE',
        ))
