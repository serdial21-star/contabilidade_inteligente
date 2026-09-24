'''Import manual de empresas externas (ADR 0013): mapeamento puro e persistência.'''

from collections.abc import Generator
from datetime import UTC, datetime
from uuid import uuid4

import pytest
from sqlalchemy.orm import Session

from serdial21.bootstrap.audit import AuditContext, audit_scope
from serdial21.bootstrap.database import Base, create_database_engine, create_session_factory
from serdial21.bootstrap.model_registry import load_models
from serdial21.bootstrap.settings import AppSettings
from serdial21.modules.access_control.adapters.outbound.persistence.models import TenantModel
from serdial21.modules.access_control.adapters.outbound.persistence.repositories import (
    SqlAlchemyCompanyImportRepository,
)
from serdial21.modules.access_control.application.services.company_import import (
    ExternalClientRecord,
    ImportExternalCompanies,
    SkippedRecord,
    map_external_client,
)
from serdial21.modules.audit.domain.entities import AuditOrigin


NOW = datetime(2026, 9, 23, 12, 0, tzinfo=UTC)


@pytest.fixture
def database_session() -> Generator[Session, None, None]:
    settings = AppSettings(_env_file=None, environment='test', database_url='sqlite+pysqlite:///:memory:')
    engine = create_database_engine(settings)
    load_models()
    Base.metadata.create_all(engine)
    session = create_session_factory(engine)()
    try:
        yield session
    finally:
        session.close()


def _tenant(session: Session) -> TenantModel:
    tenant = TenantModel(
        id=uuid4(), name='Serdial21', timezone='America/Sao_Paulo',
        currency_code='BRL', status='active',
    )
    session.add(tenant)
    with audit_scope(session, _import_context()):
        session.commit()
    return tenant


def _record(**overrides: object) -> ExternalClientRecord:
    base = dict(
        external_id='101', nome_cliente='Padaria Bom Pao Ltda', nome_fantasia='Padaria Bom Pao',
        cnpj='12345678000199', cnpj_cpf=None, status='Ativo',
    )
    base.update(overrides)
    return ExternalClientRecord(**base)  # type: ignore[arg-type]


def _import_context() -> AuditContext:
    return AuditContext(correlation_id=uuid4(), origin=AuditOrigin.IMPORT, reason='import teste')


# --- mapeamento puro -------------------------------------------------------

def test_map_active_client_uses_cnpj() -> None:
    mapped = map_external_client(_record())
    assert not isinstance(mapped, SkippedRecord)
    assert mapped.tax_identifier == '12345678000199'
    assert mapped.status == 'active'
    assert mapped.trade_name == 'Padaria Bom Pao'


def test_map_falls_back_to_cnpj_cpf_when_cnpj_missing() -> None:
    mapped = map_external_client(_record(cnpj=None, cnpj_cpf='11122233344'))
    assert not isinstance(mapped, SkippedRecord)
    assert mapped.tax_identifier == '11122233344'


def test_map_skips_lead_status() -> None:
    mapped = map_external_client(_record(status='Lead'))
    assert isinstance(mapped, SkippedRecord)
    assert mapped.reason.startswith('status_nao_mapeado')


def test_map_skips_record_without_any_tax_identifier() -> None:
    mapped = map_external_client(_record(cnpj=None, cnpj_cpf=None))
    assert isinstance(mapped, SkippedRecord)
    assert mapped.reason == 'sem_identificador_fiscal'


def test_map_canonicalizes_tax_identifier_to_digits_preserving_leading_zeros() -> None:
    mapped = map_external_client(_record(cnpj='00.123.456/0001-99'))
    assert not isinstance(mapped, SkippedRecord)
    assert mapped.tax_identifier == '00123456000199'
    cpf = map_external_client(_record(cnpj='574.431.141-68'))
    assert not isinstance(cpf, SkippedRecord) and cpf.tax_identifier == '57443114168'


def test_map_skips_tax_identifier_with_invalid_length() -> None:
    mapped = map_external_client(_record(cnpj='12345'))
    assert isinstance(mapped, SkippedRecord)
    assert mapped.reason == 'identificador_fiscal_invalido'


def test_clean_external_cell_treats_literal_null_as_empty() -> None:
    from serdial21.modules.access_control.application.services.company_import import (
        clean_external_cell,
    )
    assert clean_external_cell('NULL') is None
    assert clean_external_cell(' null ') is None
    assert clean_external_cell('') is None
    assert clean_external_cell(None) is None
    assert clean_external_cell(' Padaria ') == 'Padaria'


def test_same_person_formatted_differently_is_reported_as_duplicate(
    database_session: Session,
) -> None:
    tenant = _tenant(database_session)
    service = ImportExternalCompanies(SqlAlchemyCompanyImportRepository(database_session))
    with audit_scope(database_session, _import_context()):
        report = service.execute(tenant.id, [
            _record(external_id='16', cnpj='57443114168'),
            _record(external_id='25', cnpj='574.431.141-68'),
        ], now=NOW)
        database_session.commit()
    assert len(report.created) == 1
    assert [item.external_id for item in report.conflicts] == ['25']
    assert report.conflicts[0].reason == 'identificador_fiscal_em_uso'


# --- persistência e idempotência -------------------------------------------

def test_import_creates_company_with_audit_event(database_session: Session) -> None:
    tenant = _tenant(database_session)
    service = ImportExternalCompanies(SqlAlchemyCompanyImportRepository(database_session))
    with audit_scope(database_session, _import_context()):
        report = service.execute(tenant.id, [_record()], now=NOW)
        database_session.commit()

    assert len(report.created) == 1
    assert report.unchanged == ()
    assert report.conflicts == ()

    from serdial21.modules.audit.adapters.outbound.persistence.models import AuditEventModel
    from sqlalchemy import select
    stored = database_session.scalars(
        select(AuditEventModel).where(AuditEventModel.action == 'company.created')
    ).all()
    assert len(stored) == 1
    assert stored[0].origin == AuditOrigin.IMPORT.value


def test_import_is_idempotent_on_identical_rerun(database_session: Session) -> None:
    tenant = _tenant(database_session)
    service = ImportExternalCompanies(SqlAlchemyCompanyImportRepository(database_session))
    with audit_scope(database_session, _import_context()):
        service.execute(tenant.id, [_record()], now=NOW)
        database_session.commit()
    with audit_scope(database_session, _import_context()):
        report = service.execute(tenant.id, [_record()], now=NOW)
        database_session.commit()

    assert report.created == ()
    assert report.unchanged == ('101',)
    assert report.conflicts == ()


def test_import_reports_conflict_on_diverging_content(database_session: Session) -> None:
    tenant = _tenant(database_session)
    service = ImportExternalCompanies(SqlAlchemyCompanyImportRepository(database_session))
    with audit_scope(database_session, _import_context()):
        service.execute(tenant.id, [_record()], now=NOW)
        database_session.commit()
    with audit_scope(database_session, _import_context()):
        report = service.execute(
            tenant.id, [_record(nome_cliente='Padaria Bom Pao EIRELI')], now=NOW,
        )
        database_session.commit()

    assert report.created == ()
    assert report.unchanged == ()
    assert len(report.conflicts) == 1
    assert report.conflicts[0].reason == 'conteudo_divergente'


def test_import_reports_conflict_on_tax_identifier_collision(database_session: Session) -> None:
    tenant = _tenant(database_session)
    service = ImportExternalCompanies(SqlAlchemyCompanyImportRepository(database_session))
    with audit_scope(database_session, _import_context()):
        service.execute(tenant.id, [_record(external_id='101')], now=NOW)
        database_session.commit()
    with audit_scope(database_session, _import_context()):
        report = service.execute(
            tenant.id, [_record(external_id='202', nome_cliente='Outra Empresa')], now=NOW,
        )
        database_session.commit()

    assert report.created == ()
    assert len(report.conflicts) == 1
    assert report.conflicts[0].reason == 'identificador_fiscal_em_uso'


def test_import_is_isolated_between_tenants(database_session: Session) -> None:
    tenant_a = _tenant(database_session)
    tenant_b = TenantModel(
        id=uuid4(), name='Outro tenant', timezone='America/Sao_Paulo',
        currency_code='BRL', status='active',
    )
    database_session.add(tenant_b)
    with audit_scope(database_session, _import_context()):
        database_session.commit()

    service = ImportExternalCompanies(SqlAlchemyCompanyImportRepository(database_session))
    with audit_scope(database_session, _import_context()):
        report_a = service.execute(tenant_a.id, [_record()], now=NOW)
        report_b = service.execute(tenant_b.id, [_record()], now=NOW)
        database_session.commit()

    assert len(report_a.created) == 1
    assert len(report_b.created) == 1
    assert report_a.created[0] != report_b.created[0]
