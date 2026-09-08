from collections.abc import Generator
from datetime import UTC, datetime, timedelta
from pathlib import Path
from uuid import UUID, uuid4

import pytest
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from serdial21.bootstrap.audit import AuditContext, audit_scope
from serdial21.bootstrap.database import (
    Base,
    create_database_engine,
    create_session_factory,
)
from serdial21.bootstrap.model_registry import load_models
from serdial21.bootstrap.nfe55 import create_nfe55_runtime
from serdial21.bootstrap.settings import AppSettings
from serdial21.modules.access_control.adapters.outbound.persistence.models import (
    CompanyAccessModel,
    CompanyModel,
    PermissionModel,
    RoleBindingModel,
    RoleModel,
    RolePermissionModel,
    TenantMembershipModel,
    TenantModel,
    UserModel,
)
from serdial21.modules.access_control.application.services.authorization import (
    AccessDeniedError,
)
from serdial21.modules.audit.domain.entities import AuditOrigin
from serdial21.modules.fiscal_documents.application.services.nfe55_importer import (
    NFe55ImportRequest,
)
from serdial21.modules.intake_documents.adapters.outbound.persistence.models import (
    ArtifactReceiptModel,
    EvidenceArtifactModel,
    TransformationRunModel,
)
from serdial21.modules.intake_documents.adapters.outbound.storage.local import (
    LocalObjectStorage,
)
from serdial21.modules.intake_documents.application.services.intake import (
    IntakeContext,
    StartBatchRequest,
)


NOW = datetime(2026, 9, 4, 18, 0, tzinfo=UTC)
FIXTURE = (
    Path(__file__).resolve().parents[1]
    / 'fixtures'
    / 'nfe55'
    / 'valid_minimal.xml'
)


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


def seed_authorized_actor(
    session: Session,
) -> tuple[UUID, UUID, UUID, UUID]:
    tenant_id = uuid4()
    company_id = uuid4()
    actor_id = uuid4()
    membership_id = uuid4()
    role_id = uuid4()
    permission_id = uuid4()
    access_id = uuid4()
    with audit_scope(session, AuditContext(
        correlation_id=uuid4(),
        origin=AuditOrigin.AUTOMATION,
        actor_id=actor_id,
        reason='synthetic NF-e authorization setup',
    )):
        session.add_all([
            TenantModel(
                id=tenant_id,
                name='Synthetic tenant',
                timezone='America/Sao_Paulo',
                currency_code='BRL',
                status='active',
            ),
            UserModel(
                id=actor_id,
                provider_issuer='urn:serdial21:test',
                provider_subject=f'synthetic-{actor_id}',
                display_name='Synthetic actor',
                is_active=True,
            ),
            PermissionModel(
                id=permission_id,
                code='company.manage',
                description='company.manage',
                version=1,
                is_active=True,
            ),
        ])
        session.flush()
        session.add_all([
            CompanyModel(
                id=company_id,
                tenant_id=tenant_id,
                legal_name='Synthetic company',
                tax_identifier='12345678000195',
                timezone='America/Sao_Paulo',
                currency_code='BRL',
                status='active',
                valid_from=NOW - timedelta(days=1),
            ),
            TenantMembershipModel(
                id=membership_id,
                tenant_id=tenant_id,
                user_id=actor_id,
                status='active',
                relationship_type='employee',
                valid_from=NOW - timedelta(days=1),
                revision=1,
            ),
            RoleModel(
                id=role_id,
                tenant_id=tenant_id,
                name='nfe-importer',
                is_active=True,
            ),
        ])
        session.flush()
        session.add_all([
            CompanyAccessModel(
                id=access_id,
                tenant_id=tenant_id,
                membership_id=membership_id,
                company_id=company_id,
                status='active',
                valid_from=NOW - timedelta(days=1),
            ),
            RolePermissionModel(
                tenant_id=tenant_id,
                role_id=role_id,
                permission_id=permission_id,
            ),
            RoleBindingModel(
                tenant_id=tenant_id,
                membership_id=membership_id,
                role_id=role_id,
                company_id=company_id,
                status='active',
                valid_from=NOW - timedelta(days=1),
            ),
        ])
        session.commit()
    return tenant_id, company_id, actor_id, access_id


def context(tenant_id: UUID, company_id: UUID, actor_id: UUID) -> IntakeContext:
    return IntakeContext(
        tenant_id=tenant_id,
        company_id=company_id,
        actor_id=actor_id,
        origin=AuditOrigin.HUMAN,
        correlation_id=uuid4(),
    )


def settings(storage_root: Path, *, max_xml_bytes: int) -> AppSettings:
    return AppSettings(
        _env_file=None,
        environment='test',
        database_url='sqlite+pysqlite:///:memory:',
        object_storage_path=storage_root,
        nfe_max_xml_bytes=max_xml_bytes,
    )


def test_runtime_applies_configured_xml_limit_and_preserves_evidence(
    database_session: Session,
    tmp_path: Path,
) -> None:
    tenant_id, company_id, actor_id, _ = seed_authorized_actor(database_session)
    runtime = create_nfe55_runtime(
        database_session,
        settings(tmp_path, max_xml_bytes=32),
        clock=lambda: NOW,
    )
    ctx = context(tenant_id, company_id, actor_id)
    batch = runtime.intake.start_batch(ctx, StartBatchRequest(
        source='NFE55_XML',
        idempotency_key='configured-limit',
    ))
    content = FIXTURE.read_bytes()

    result = runtime.importer.import_xml(ctx, NFe55ImportRequest(
        batch_id=batch.id,
        content=content,
        original_filename='oversized.xml',
    ))
    database_session.commit()

    assert result.status == 'QUARANTINED'
    assert result.issue_codes == ('XML_TOO_LARGE',)
    run = database_session.get(
        TransformationRunModel,
        result.transformation_run_id,
    )
    artifact = database_session.get(EvidenceArtifactModel, result.artifact_id)
    assert run is not None and run.status == 'FAILED'
    assert artifact is not None
    assert LocalObjectStorage(tmp_path).read(artifact.storage_key) == content


def test_runtime_revalidates_real_company_access_before_import(
    database_session: Session,
    tmp_path: Path,
) -> None:
    tenant_id, company_id, actor_id, access_id = seed_authorized_actor(
        database_session
    )
    runtime = create_nfe55_runtime(
        database_session,
        settings(tmp_path, max_xml_bytes=5 * 1024 * 1024),
        clock=lambda: NOW,
    )
    ctx = context(tenant_id, company_id, actor_id)
    batch = runtime.intake.start_batch(ctx, StartBatchRequest(
        source='NFE55_XML',
        idempotency_key='revoked-access',
    ))
    database_session.commit()
    access = database_session.get(CompanyAccessModel, access_id)
    assert access is not None
    access.status = 'revoked'
    database_session.commit()

    with pytest.raises(AccessDeniedError, match='access denied'):
        runtime.importer.import_xml(ctx, NFe55ImportRequest(
            batch_id=batch.id,
            content=FIXTURE.read_bytes(),
            original_filename='denied.xml',
        ))
    database_session.rollback()

    assert database_session.scalar(
        select(func.count()).select_from(ArtifactReceiptModel)
    ) == 0
    assert list(tmp_path.rglob('*')) == []
