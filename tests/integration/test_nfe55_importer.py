from collections.abc import Generator
from datetime import UTC, datetime
from decimal import Decimal
from hashlib import sha256
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
from serdial21.modules.fiscal_documents.adapters.inbound.nfe55_xml import (
    SafeNFe55XmlParser,
)
from serdial21.modules.fiscal_documents.adapters.outbound.persistence.models import (
    CanonicalRecordModel,
    FiscalDocumentItemModel,
    FiscalDocumentModel,
    ImmutableFiscalRecordError,
    TaxDetailModel,
)
from serdial21.modules.fiscal_documents.adapters.outbound.persistence.repositories import (
    SqlAlchemyFiscalDocumentRepository,
)
from serdial21.modules.fiscal_documents.application.services.nfe55_importer import (
    NFe55ImportRequest,
    NFe55ImportService,
)
from serdial21.modules.intake_documents.adapters.outbound.persistence.models import (
    ArtifactReceiptModel,
    EvidenceArtifactModel,
    ImmutableDocumentError,
    TransformationRunModel,
    ValidationIssueModel,
    LineageEdgeModel,
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
    StartBatchRequest,
)


NOW = datetime(2026, 9, 4, 18, 0, tzinfo=UTC)
FIXTURES = Path(__file__).resolve().parents[1] / 'fixtures' / 'nfe55'


class AllowDocumentAuthorization:
    def require_company_manage(
        self,
        tenant_id: UUID,
        company_id: UUID,
        actor_id: UUID | None,
        *,
        at: datetime,
    ) -> None:
        assert tenant_id and company_id and actor_id and at == NOW


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
    with audit_scope(session, AuditContext(
        correlation_id=uuid4(),
        origin=AuditOrigin.AUTOMATION,
        actor_id=uuid4(),
        reason='synthetic NF-e test setup',
    )):
        if session.get(TenantModel, tenant_id) is None:
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


def context(tenant_id: UUID, company_id: UUID) -> IntakeContext:
    return IntakeContext(
        tenant_id=tenant_id,
        company_id=company_id,
        actor_id=uuid4(),
        origin=AuditOrigin.HUMAN,
        correlation_id=uuid4(),
    )


def services(
    session: Session,
    storage_root: Path,
) -> tuple[DocumentIntakeService, NFe55ImportService]:
    audit = AuditService(SqlAlchemyAuditRepository(session), clock=lambda: NOW)
    intake = DocumentIntakeService(
        SqlAlchemyIntakeRepository(session),
        LocalObjectStorage(storage_root),
        audit,
        AllowDocumentAuthorization(),
        clock=lambda: NOW,
    )
    importer = NFe55ImportService(
        intake,
        SafeNFe55XmlParser(),
        SqlAlchemyFiscalDocumentRepository(session),
        audit,
        clock=lambda: NOW,
    )
    return intake, importer


def batch_id(intake: DocumentIntakeService, ctx: IntakeContext, key: str) -> UUID:
    return intake.start_batch(ctx, StartBatchRequest(
        source='NFE55_XML',
        idempotency_key=key,
    )).id


def fixture(name: str) -> bytes:
    return (FIXTURES / name).read_bytes()


def request(batch: UUID, content: bytes, filename: str = 'nfe.xml') -> NFe55ImportRequest:
    return NFe55ImportRequest(
        batch_id=batch,
        content=content,
        original_filename=filename,
    )


def test_imports_valid_nfe55_with_items_taxes_and_canonical_lineage(
    database_session: Session,
    tmp_path: Path,
) -> None:
    tenant_id, company_id = uuid4(), uuid4()
    seed_company(database_session, tenant_id, company_id)
    ctx = context(tenant_id, company_id)
    intake, importer = services(database_session, tmp_path)

    result = importer.import_xml(
        ctx,
        request(batch_id(intake, ctx, 'valid'), fixture('valid_minimal.xml')),
    )
    database_session.commit()

    assert result.status == 'IMPORTED'
    document = database_session.get(FiscalDocumentModel, result.fiscal_document_id)
    assert document is not None
    assert document.access_key == '35260912345678000195550010000000011000000011'
    assert document.model == '55'
    assert document.schema_version == '4.00'
    assert document.issuer_tax_id == '12345678000195'
    assert document.recipient_tax_id == '98765432000198'
    assert document.issued_at == datetime(2026, 9, 4, 13, 0, tzinfo=UTC)
    assert document.products_total == Decimal('100.00')
    assert document.freight_total == Decimal('0.00')
    assert document.insurance_total == Decimal('0.00')
    assert document.discount_total == Decimal('0.00')
    assert document.other_total == Decimal('0.00')
    assert document.tax_total == Decimal('27.25')
    assert document.invoice_total == Decimal('100.00')
    item = database_session.scalar(select(FiscalDocumentItemModel))
    assert item is not None
    assert item.sequence == 1
    assert item.product_code == 'PROD-001'
    assert item.cfop == '5102'
    assert item.quantity == Decimal('2.000000')
    assert item.unit_value == Decimal('50.0000000000')
    assert item.gross_total == Decimal('100.00')
    taxes = list(database_session.scalars(
        select(TaxDetailModel).order_by(TaxDetailModel.tax_type)
    ))
    assert [(tax.tax_type, tax.tax_status, tax.amount) for tax in taxes] == [
        ('COFINS', '01', Decimal('7.60')),
        ('ICMS', '00', Decimal('18.00')),
        ('PIS', '01', Decimal('1.65')),
    ]
    run = database_session.get(TransformationRunModel, result.transformation_run_id)
    assert run is not None
    assert (run.parser_name, run.parser_version, run.schema_version) == (
        'serdial21.nfe55.xml', '1.1.0', '4.00'
    )
    expected_hash = sha256(fixture('valid_minimal.xml')).hexdigest()
    assert run.input_hash == expected_hash == result.content_hash
    assert run.output_hash is not None and len(run.output_hash) == 64
    canonical = database_session.get(CanonicalRecordModel, result.canonical_record_id)
    assert canonical is not None
    assert canonical.source_hash == result.content_hash
    assert canonical.schema_version == 'serdial21.fiscal.nfe55/v1'
    assert canonical.status == 'STRUCTURALLY_VALIDATED'
    artifact = database_session.get(EvidenceArtifactModel, result.artifact_id)
    receipt = database_session.get(ArtifactReceiptModel, result.receipt_id)
    assert artifact is not None and receipt is not None
    assert artifact.content_hash == expected_hash
    assert receipt.artifact_id == artifact.id
    assert LocalObjectStorage(tmp_path).read(artifact.storage_key) == fixture(
        'valid_minimal.xml'
    )
    lineages = {
        (edge.source_type, edge.target_type, edge.relation)
        for edge in database_session.scalars(select(LineageEdgeModel))
    }
    assert lineages == {
        ('EvidenceArtifact', 'TransformationRun', 'TRANSFORMED_BY'),
        ('ArtifactReceipt', 'TransformationRun', 'PROCESSED_BY'),
        ('TransformationRun', 'CanonicalRecord', 'NORMALIZED_TO'),
        ('CanonicalRecord', 'FiscalDocument', 'TYPED_AS'),
    }


def test_imported_fiscal_document_is_immutable(
    database_session: Session,
    tmp_path: Path,
) -> None:
    tenant_id, company_id = uuid4(), uuid4()
    seed_company(database_session, tenant_id, company_id)
    ctx = context(tenant_id, company_id)
    intake, importer = services(database_session, tmp_path)
    result = importer.import_xml(
        ctx,
        request(batch_id(intake, ctx, 'immutable'), fixture('valid_minimal.xml')),
    )
    database_session.commit()

    document = database_session.get(FiscalDocumentModel, result.fiscal_document_id)
    assert document is not None
    document.observed_status = 'CHANGED'
    with pytest.raises(ImmutableFiscalRecordError):
        database_session.commit()
    database_session.rollback()


def test_same_key_and_hash_is_idempotent_but_preserves_receipt(
    database_session: Session,
    tmp_path: Path,
) -> None:
    tenant_id, company_id = uuid4(), uuid4()
    seed_company(database_session, tenant_id, company_id)
    ctx = context(tenant_id, company_id)
    intake, importer = services(database_session, tmp_path)
    content = fixture('valid_minimal.xml')

    first = importer.import_xml(
        ctx,
        request(batch_id(intake, ctx, 'duplicate-first'), content, 'first.xml'),
    )
    database_session.commit()
    second = importer.import_xml(
        ctx,
        request(batch_id(intake, ctx, 'duplicate-second'), content, 'second.xml'),
    )
    database_session.commit()

    assert first.status == 'IMPORTED'
    assert second.status == 'IDEMPOTENT_REDELIVERY'
    assert second.fiscal_document_id == first.fiscal_document_id
    assert database_session.scalar(
        select(func.count()).select_from(FiscalDocumentModel)
    ) == 1
    assert database_session.scalar(
        select(func.count()).select_from(ArtifactReceiptModel)
    ) == 2


def test_same_access_key_with_different_hash_is_quarantined(
    database_session: Session,
    tmp_path: Path,
) -> None:
    tenant_id, company_id = uuid4(), uuid4()
    seed_company(database_session, tenant_id, company_id)
    ctx = context(tenant_id, company_id)
    intake, importer = services(database_session, tmp_path)
    original = fixture('valid_minimal.xml')
    changed = original.replace(b'PRODUTO SINTETICO', b'PRODUTO ALTERADO')

    first = importer.import_xml(
        ctx,
        request(batch_id(intake, ctx, 'conflict-first'), original, 'original.xml'),
    )
    database_session.commit()
    conflict = importer.import_xml(
        ctx,
        request(batch_id(intake, ctx, 'conflict-second'), changed, 'changed.xml'),
    )
    database_session.commit()

    assert first.status == 'IMPORTED'
    assert conflict.status == 'CONFLICT_QUARANTINED'
    assert conflict.issue_codes == ('NFE_ACCESS_KEY_HASH_CONFLICT',)
    assert database_session.scalar(
        select(func.count()).select_from(EvidenceArtifactModel)
    ) == 2
    assert database_session.scalar(
        select(func.count()).select_from(FiscalDocumentModel)
    ) == 1
    issue = database_session.scalar(select(ValidationIssueModel).where(
        ValidationIssueModel.code == 'NFE_ACCESS_KEY_HASH_CONFLICT'
    ))
    assert issue is not None
    assert issue.resolution_status == 'QUARANTINED'
    failed_run = database_session.get(
        TransformationRunModel,
        conflict.transformation_run_id,
    )
    assert failed_run is not None
    assert failed_run.artifact_id == conflict.artifact_id
    assert failed_run.input_hash == conflict.content_hash
    conflict_edge = database_session.scalar(select(LineageEdgeModel).where(
        LineageEdgeModel.relation == 'CONFLICTS_WITH'
    ))
    assert conflict_edge is not None
    assert conflict_edge.target_id == first.fiscal_document_id


@pytest.mark.parametrize(
    ('content', 'expected_code'),
    [
        (b'<NFe>', 'MALFORMED_XML'),
        (
            b'<!DOCTYPE x [<!ENTITY bomb \'boom\'>]><x>&bomb;</x>',
            'UNSAFE_XML_DECLARATION',
        ),
    ],
)
def test_invalid_or_malicious_content_is_preserved_and_quarantined(
    database_session: Session,
    tmp_path: Path,
    content: bytes,
    expected_code: str,
) -> None:
    tenant_id, company_id = uuid4(), uuid4()
    seed_company(database_session, tenant_id, company_id)
    ctx = context(tenant_id, company_id)
    intake, importer = services(database_session, tmp_path)

    result = importer.import_xml(
        ctx,
        request(batch_id(intake, ctx, expected_code), content),
    )
    database_session.commit()

    assert result.status == 'QUARANTINED'
    assert result.issue_codes == (expected_code,)
    assert database_session.get(EvidenceArtifactModel, result.artifact_id) is not None
    assert database_session.scalar(
        select(func.count()).select_from(FiscalDocumentModel)
    ) == 0
    run = database_session.get(TransformationRunModel, result.transformation_run_id)
    assert run is not None and run.status == 'FAILED'


def test_missing_field_is_not_invented_and_creates_validation_issue(
    database_session: Session,
    tmp_path: Path,
) -> None:
    tenant_id, company_id = uuid4(), uuid4()
    seed_company(database_session, tenant_id, company_id)
    ctx = context(tenant_id, company_id)
    intake, importer = services(database_session, tmp_path)

    result = importer.import_xml(
        ctx,
        request(batch_id(intake, ctx, 'missing'), fixture('missing_recipient.xml')),
    )
    database_session.commit()

    assert result.status == 'IMPORTED'
    document = database_session.get(FiscalDocumentModel, result.fiscal_document_id)
    assert document is not None
    assert document.recipient_tax_id is None
    assert document.recipient_name is None
    paths = set(database_session.scalars(select(ValidationIssueModel.field_path)))
    assert {'recipient.tax_id', 'recipient.name'} <= paths


@pytest.mark.parametrize(
    ('old_value', 'new_value', 'expected_code'),
    [
        (b'<vNF>100.00</vNF>', b'<vNF>NaN</vNF>', 'INVALID_DECIMAL'),
        (
            b'<vNF>100.00</vNF>',
            b'<vNF>100.001</vNF>',
            'DECIMAL_OUT_OF_RANGE',
        ),
        (
            b'<indTot>1</indTot>',
            b'<indTot>invalid</indTot>',
            'INVALID_BOOLEAN',
        ),
    ],
)
def test_invalid_typed_value_is_quarantined_before_persistence(
    database_session: Session,
    tmp_path: Path,
    old_value: bytes,
    new_value: bytes,
    expected_code: str,
) -> None:
    tenant_id, company_id = uuid4(), uuid4()
    seed_company(database_session, tenant_id, company_id)
    ctx = context(tenant_id, company_id)
    intake, importer = services(database_session, tmp_path)
    content = fixture('valid_minimal.xml').replace(old_value, new_value)

    result = importer.import_xml(
        ctx,
        request(batch_id(intake, ctx, expected_code), content),
    )
    database_session.commit()

    assert result.status == 'QUARANTINED'
    assert expected_code in result.issue_codes
    assert database_session.scalar(
        select(func.count()).select_from(FiscalDocumentModel)
    ) == 0
    issue = database_session.scalar(select(ValidationIssueModel).where(
        ValidationIssueModel.code == expected_code
    ))
    assert issue is not None and issue.severity == 'ERROR'


def test_failed_transformation_is_immutable(
    database_session: Session,
    tmp_path: Path,
) -> None:
    tenant_id, company_id = uuid4(), uuid4()
    seed_company(database_session, tenant_id, company_id)
    ctx = context(tenant_id, company_id)
    intake, importer = services(database_session, tmp_path)
    result = importer.import_xml(
        ctx,
        request(batch_id(intake, ctx, 'terminal-run'), b'<NFe>'),
    )
    database_session.commit()

    run = database_session.get(
        TransformationRunModel,
        result.transformation_run_id,
    )
    assert run is not None and run.status == 'FAILED'
    run.status = 'STARTED'
    with pytest.raises(ImmutableDocumentError):
        database_session.commit()
    database_session.rollback()

    run = database_session.get(
        TransformationRunModel,
        result.transformation_run_id,
    )
    assert run is not None
    database_session.delete(run)
    with pytest.raises(ImmutableDocumentError):
        database_session.commit()
    database_session.rollback()


def test_same_key_is_isolated_between_tenants(
    database_session: Session,
    tmp_path: Path,
) -> None:
    tenant_a, company_a = uuid4(), uuid4()
    tenant_b, company_b = uuid4(), uuid4()
    seed_company(database_session, tenant_a, company_a)
    seed_company(database_session, tenant_b, company_b)
    intake, importer = services(database_session, tmp_path)
    context_a = context(tenant_a, company_a)
    context_b = context(tenant_b, company_b)
    content = fixture('valid_minimal.xml')

    result_a = importer.import_xml(
        context_a,
        request(batch_id(intake, context_a, 'tenant-a'), content),
    )
    result_b = importer.import_xml(
        context_b,
        request(batch_id(intake, context_b, 'tenant-b'), content),
    )
    database_session.commit()

    assert result_a.status == result_b.status == 'IMPORTED'
    assert result_a.fiscal_document_id != result_b.fiscal_document_id
    assert result_a.artifact_id != result_b.artifact_id
    assert database_session.scalar(
        select(func.count()).select_from(FiscalDocumentModel)
    ) == 2


def test_same_key_is_isolated_between_companies_in_one_tenant(
    database_session: Session,
    tmp_path: Path,
) -> None:
    tenant_id = uuid4()
    company_a, company_b = uuid4(), uuid4()
    seed_company(database_session, tenant_id, company_a)
    seed_company(database_session, tenant_id, company_b)
    intake, importer = services(database_session, tmp_path)
    context_a = context(tenant_id, company_a)
    context_b = context(tenant_id, company_b)
    content = fixture('valid_minimal.xml')

    result_a = importer.import_xml(
        context_a,
        request(batch_id(intake, context_a, 'company-a'), content),
    )
    result_b = importer.import_xml(
        context_b,
        request(batch_id(intake, context_b, 'company-b'), content),
    )
    database_session.commit()

    assert result_a.status == result_b.status == 'IMPORTED'
    assert result_a.artifact_id == result_b.artifact_id
    assert result_a.fiscal_document_id != result_b.fiscal_document_id
    assert database_session.scalar(
        select(func.count()).select_from(FiscalDocumentModel)
    ) == 2


def test_batch_id_from_another_tenant_is_uniformly_unavailable(
    database_session: Session,
    tmp_path: Path,
) -> None:
    tenant_a, company_a = uuid4(), uuid4()
    tenant_b, company_b = uuid4(), uuid4()
    seed_company(database_session, tenant_a, company_a)
    seed_company(database_session, tenant_b, company_b)
    intake, importer = services(database_session, tmp_path)
    context_a = context(tenant_a, company_a)
    context_b = context(tenant_b, company_b)
    foreign_batch = batch_id(intake, context_a, 'foreign-batch')

    with pytest.raises(
        IntakeResourceUnavailableError,
        match='resource unavailable',
    ):
        importer.import_xml(
            context_b,
            request(foreign_batch, fixture('valid_minimal.xml')),
        )
    database_session.rollback()

    assert database_session.scalar(
        select(func.count()).select_from(ArtifactReceiptModel)
    ) == 0
    assert database_session.scalar(
        select(func.count()).select_from(FiscalDocumentModel)
    ) == 0
