"""Prova vertical sem regra inventada e sem arquivo Domínio artificial."""
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

import pytest
from sqlalchemy import select

from serdial21.bootstrap.audit import AuditContext, audit_scope
from serdial21.bootstrap.database import Base, create_database_engine, create_session_factory
from serdial21.bootstrap.model_registry import load_models
from serdial21.bootstrap.settings import AppSettings
from serdial21.modules.access_control.adapters.outbound.persistence.models import CompanyModel, TenantModel
from serdial21.modules.audit.adapters.outbound.persistence.repositories import SqlAlchemyAuditRepository
from serdial21.modules.audit.application.services.audit import AuditService
from serdial21.modules.audit.domain.entities import AuditOrigin
from serdial21.modules.fiscal_documents.adapters.inbound.nfe55_xml import SafeNFe55XmlParser
from serdial21.modules.fiscal_documents.adapters.outbound.persistence.repositories import SqlAlchemyFiscalDocumentRepository
from serdial21.modules.fiscal_documents.application.services.nfe55_importer import NFe55ImportRequest, NFe55ImportService
from serdial21.modules.intake_documents.adapters.outbound.persistence.repositories import SqlAlchemyIntakeRepository
from serdial21.modules.intake_documents.adapters.outbound.storage.local import LocalObjectStorage
from serdial21.modules.intake_documents.application.services.intake import DocumentIntakeService, IntakeContext, StartBatchRequest
from serdial21.modules.workflow.adapters.outbound.persistence.models import AuthorizedEffectModel, PreHomologationExportBatchModel, WorkItemModel
from serdial21.modules.workflow.application.services.pre_homologation import BLOCK_REASONS, JourneyResourceUnavailableError, PreHomologationContext, PreHomologationJourneyService

NOW = datetime(2026, 9, 6, 12, tzinfo=UTC)
FIXTURE = Path(__file__).parents[1] / 'fixtures' / 'nfe55' / 'valid_minimal.xml'

class Authorization:
    def require_company_manage(self, *args: object, **kwargs: object) -> None: pass

def make_session():
    settings = AppSettings(_env_file=None, environment='test', database_url='sqlite+pysqlite:///:memory:')
    engine = create_database_engine(settings); load_models()
    # Model registry is intentionally extended by its migration rollout; direct import
    # preserves this isolated contract test while the bootstrap change is pending.
    from serdial21.modules.workflow.adapters.outbound.persistence import models as workflow_models
    _ = workflow_models
    Base.metadata.create_all(engine)
    return create_session_factory(engine)(), engine

def seed(session, tenant_id, company_id):
    with audit_scope(session, AuditContext(uuid4(), AuditOrigin.AUTOMATION, uuid4(), reason='test setup')):
        session.add(TenantModel(id=tenant_id,name='Tenant',timezone='America/Sao_Paulo',currency_code='BRL',status='active'))
        session.flush()
        session.add(CompanyModel(id=company_id,tenant_id=tenant_id,legal_name='Company',tax_identifier=company_id.hex[:14],timezone='America/Sao_Paulo',currency_code='BRL',status='active',valid_from=NOW))
        session.commit()

def import_nfe(session, tmp_path, tenant_id, company_id):
    audit = AuditService(SqlAlchemyAuditRepository(session), clock=lambda: NOW)
    intake = DocumentIntakeService(SqlAlchemyIntakeRepository(session),LocalObjectStorage(tmp_path),audit,Authorization(),clock=lambda: NOW)
    ctx = IntakeContext(tenant_id,company_id,uuid4(),AuditOrigin.HUMAN,uuid4())
    batch = intake.start_batch(ctx, StartBatchRequest(source='NFE55_XML',idempotency_key='e2e')).id
    importer = NFe55ImportService(intake,SafeNFe55XmlParser(),SqlAlchemyFiscalDocumentRepository(session),audit,clock=lambda: NOW)
    result = importer.import_xml(ctx,NFe55ImportRequest(batch,FIXTURE.read_bytes(),'synthetic-nfe.xml'))
    session.commit(); return result, audit

def test_nfe_reaches_only_blocked_for_homologation_and_reverse_trace(tmp_path):
    session, engine = make_session(); tenant_id, company_id = uuid4(), uuid4()
    try:
        seed(session,tenant_id,company_id); result,audit = import_nfe(session,tmp_path,tenant_id,company_id)
        correlation_id = uuid4()
        journey = PreHomologationJourneyService(session,audit,clock=lambda: NOW).create_blocked_intent(PreHomologationContext(tenant_id,company_id,uuid4(),correlation_id,AuditOrigin.HUMAN),fiscal_document_id=result.fiscal_document_id)
        session.commit()
        assert journey.status == 'BLOCKED_FOR_HOMOLOGATION'
        assert journey.block_reasons == BLOCK_REASONS
        item = session.get(WorkItemModel,journey.work_item_id); effect = session.get(AuthorizedEffectModel,journey.authorized_effect_id); batch = session.get(PreHomologationExportBatchModel,journey.export_batch_id)
        assert item.status == 'OPEN' and item.work_type == 'RULE_EVALUATION_REQUIRED'
        assert effect.authorization_status == 'PENDING' and effect.execution_status == 'NOT_EXECUTED'
        assert batch is not None and batch.fiscal_document_id == result.fiscal_document_id and batch.canonical_record_id == result.canonical_record_id and batch.artifact_id == result.artifact_id
        assert batch.connector_name == 'DOMINIO' and batch.status == 'BLOCKED_FOR_HOMOLOGATION'
        events = audit.list_by_correlation(tenant_id,correlation_id)
        assert {event.action for event in events} >= {'workflow_case.created','work_item.created','approval_request.pending','authorized_effect.pending','export_batch.blocked_for_homologation'}
    finally:
        session.close(); Base.metadata.drop_all(engine); engine.dispose()

def test_foreign_fiscal_document_is_uniformly_unavailable(tmp_path):
    session, engine = make_session(); tenant_a,company_a,tenant_b,company_b = uuid4(),uuid4(),uuid4(),uuid4()
    try:
        seed(session,tenant_a,company_a); seed(session,tenant_b,company_b); result,audit = import_nfe(session,tmp_path,tenant_a,company_a)
        service = PreHomologationJourneyService(session,audit,clock=lambda: NOW)
        with pytest.raises(JourneyResourceUnavailableError,match='resource unavailable'):
            service.create_blocked_intent(PreHomologationContext(tenant_b,company_b,uuid4(),uuid4(),AuditOrigin.API),fiscal_document_id=result.fiscal_document_id)
    finally:
        session.rollback(); session.close(); Base.metadata.drop_all(engine); engine.dispose()
