'''Import manual da equipe interna e vínculo com empresas (ADR 0013, item 2).'''

from collections.abc import Generator
from datetime import UTC, datetime
from uuid import uuid4

import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session

from serdial21.bootstrap.audit import AuditContext, audit_scope
from serdial21.bootstrap.database import Base, create_database_engine, create_session_factory
from serdial21.bootstrap.model_registry import load_models
from serdial21.bootstrap.settings import AppSettings
from serdial21.modules.access_control.adapters.outbound.persistence.models import (
    CompanyTeamAssignmentModel,
    TenantModel,
)
from serdial21.modules.access_control.adapters.outbound.persistence.repositories import (
    SqlAlchemyCompanyImportRepository,
    SqlAlchemyTeamImportRepository,
)
from serdial21.modules.access_control.application.services.company_import import (
    ExternalClientRecord,
    ImportExternalCompanies,
    SkippedRecord,
)
from serdial21.modules.access_control.application.services.team_import import (
    AssignResponsibleFromExternalClients,
    ExternalResponsibleRecord,
    ExternalStaffRecord,
    ImportExternalTeam,
    map_external_staff,
    normalize_person_name,
)
from serdial21.modules.audit.adapters.outbound.persistence.models import AuditEventModel
from serdial21.modules.audit.domain.entities import AuditOrigin


NOW = datetime(2026, 9, 23, 12, 0, tzinfo=UTC)


@pytest.fixture
def session() -> Generator[Session, None, None]:
    settings = AppSettings(_env_file=None, environment='test', database_url='sqlite+pysqlite:///:memory:')
    engine = create_database_engine(settings)
    load_models()
    Base.metadata.create_all(engine)
    db = create_session_factory(engine)()
    try:
        yield db
    finally:
        db.close()


def _ctx() -> AuditContext:
    return AuditContext(correlation_id=uuid4(), origin=AuditOrigin.IMPORT, reason='teste')


def _tenant(db: Session, name: str = 'Serdial21') -> TenantModel:
    tenant = TenantModel(
        id=uuid4(), name=name, timezone='America/Sao_Paulo', currency_code='BRL', status='active',
    )
    db.add(tenant)
    with audit_scope(db, _ctx()):
        db.commit()
    return tenant


def _staff(**overrides: object) -> ExternalStaffRecord:
    base = dict(external_id='7', nome_funcionario='Maria  da Silva', email='Maria@Serdial21.com',
                cargo='Contadora', status='Ativo')
    base.update(overrides)
    return ExternalStaffRecord(**base)  # type: ignore[arg-type]


def _run_team(db: Session, tenant: TenantModel, records: list[ExternalStaffRecord]):
    with audit_scope(db, _ctx()):
        report = ImportExternalTeam(SqlAlchemyTeamImportRepository(db)).execute(
            tenant.id, records, now=NOW)
        db.commit()
    return report


def _company(db: Session, tenant: TenantModel, external_id: str = '1', cnpj: str = '12345678000199'):
    with audit_scope(db, _ctx()):
        ImportExternalCompanies(SqlAlchemyCompanyImportRepository(db)).execute(
            tenant.id,
            [ExternalClientRecord(external_id, 'Empresa X', None, cnpj, None, 'Ativo')],
            now=NOW)
        db.commit()


def _assign(db: Session, tenant: TenantModel, records: list[ExternalResponsibleRecord]):
    with audit_scope(db, _ctx()):
        report = AssignResponsibleFromExternalClients(SqlAlchemyTeamImportRepository(db)).execute(
            tenant.id, records, now=NOW)
        db.commit()
    return report


# --- mapeamento puro -------------------------------------------------------

def test_map_staff_normalizes_and_never_carries_password() -> None:
    mapped = map_external_staff(_staff())
    assert not isinstance(mapped, SkippedRecord)
    assert mapped.display_name == 'Maria da Silva'
    assert mapped.email == 'maria@serdial21.com'
    assert mapped.status == 'active'
    assert not hasattr(mapped, 'senha')


def test_map_staff_skips_unknown_status_and_empty_name() -> None:
    assert isinstance(map_external_staff(_staff(status='Afastado')), SkippedRecord)
    assert isinstance(map_external_staff(_staff(nome_funcionario='   ')), SkippedRecord)


def test_name_normalization_ignores_case_accents_and_spacing() -> None:
    assert normalize_person_name('  JOSÉ   da Conceição ') == normalize_person_name('jose da conceicao')


# --- equipe ----------------------------------------------------------------

def test_team_import_creates_member_with_audit_and_is_idempotent(session: Session) -> None:
    tenant = _tenant(session)
    first = _run_team(session, tenant, [_staff()])
    second = _run_team(session, tenant, [_staff()])
    assert len(first.created) == 1
    assert second.created == () and second.unchanged == ('7',)
    events = session.scalars(select(AuditEventModel).where(
        AuditEventModel.action == 'office_team_member.created')).all()
    assert len(events) == 1
    assert events[0].origin == AuditOrigin.IMPORT.value
    trail = str(events[0].after_state).lower()
    assert 'maria' not in trail and 'serdial21.com' not in trail  # sem nome/e-mail na trilha
    assert events[0].after_state['job_title'] == 'Contadora'


def test_team_import_conflicts_on_divergence_and_email_collision(session: Session) -> None:
    tenant = _tenant(session)
    _run_team(session, tenant, [_staff()])
    diverging = _run_team(session, tenant, [_staff(cargo='Gerente')])
    collision = _run_team(session, tenant, [_staff(external_id='8', nome_funcionario='Outra')])
    assert diverging.conflicts[0].reason == 'conteudo_divergente'
    assert collision.conflicts[0].reason == 'email_em_uso'


def test_team_import_is_isolated_between_tenants(session: Session) -> None:
    a, b = _tenant(session), _tenant(session, 'Outro')
    assert len(_run_team(session, a, [_staff()]).created) == 1
    assert len(_run_team(session, b, [_staff()]).created) == 1  # mesmo e-mail/id, outro tenant


# --- vínculo empresa -> responsável ----------------------------------------

def test_assignment_matches_exact_normalized_name_and_is_idempotent(session: Session) -> None:
    tenant = _tenant(session)
    _run_team(session, tenant, [_staff()])
    _company(session, tenant)
    record = ExternalResponsibleRecord('1', 'MARIA da silva')
    first = _assign(session, tenant, [record])
    second = _assign(session, tenant, [record])
    assert len(first.created) == 1
    assert second.created == () and second.unchanged == ('1',)
    stored = session.scalars(select(CompanyTeamAssignmentModel)).all()
    assert len(stored) == 1 and stored[0].role_label == 'responsavel'
    audited = session.scalars(select(AuditEventModel).where(
        AuditEventModel.action == 'company_team_assignment.created')).all()
    assert len(audited) == 1 and audited[0].company_id == stored[0].company_id


def test_assignment_never_guesses(session: Session) -> None:
    tenant = _tenant(session)
    _run_team(session, tenant, [
        _staff(external_id='7', email='a@x.com'),
        _staff(external_id='8', email='b@x.com', nome_funcionario='maria da silva'),  # homônimo
        _staff(external_id='9', email='c@x.com', nome_funcionario='Pedro Souza', status='Inativo'),
    ])
    for external_id, cnpj in (('1', '11111111000111'), ('2', '22222222000122'),
                              ('3', '33333333000133'), ('4', '44444444000144')):
        _company(session, tenant, external_id, cnpj)
    report = _assign(session, tenant, [
        ExternalResponsibleRecord('1', 'Maria da Silva'),   # ambíguo (2 homônimos)
        ExternalResponsibleRecord('2', 'Maria'),            # aproximação NÃO casa
        ExternalResponsibleRecord('3', 'Pedro Souza'),      # membro inativo
        ExternalResponsibleRecord('4', None),               # sem responsável
        ExternalResponsibleRecord('99', 'Maria da Silva'),  # empresa não importada
    ])
    assert report.created == ()
    assert report.ambiguous == ('1',)
    assert report.unmatched == ('2',)
    assert report.inactive_member == ('3',)
    assert report.without_responsible == ('4',)
    assert report.company_missing == ('99',)
    assert session.scalars(select(CompanyTeamAssignmentModel)).all() == []


def test_assignment_does_not_cross_tenants(session: Session) -> None:
    a, b = _tenant(session), _tenant(session, 'Outro')
    _run_team(session, a, [_staff()])
    _company(session, b)  # empresa existe só no tenant B
    report = _assign(session, b, [ExternalResponsibleRecord('1', 'Maria da Silva')])
    assert report.created == () and report.unmatched == ('1',)  # membro do tenant A é invisível
