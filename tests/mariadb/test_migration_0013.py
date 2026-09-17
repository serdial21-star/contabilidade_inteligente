'''Homologação isolada da migration 0013 no Migration Lab autorizado.'''

from __future__ import annotations

import os
from datetime import UTC, date, datetime
from uuid import uuid4

import pytest
from alembic import command
from alembic.config import Config
from dotenv import dotenv_values
from sqlalchemy import delete, inspect, select, text

from serdial21.modules.access_control.adapters.outbound.persistence.models import (
    CompanyModel,
    TenantModel,
    UserModel,
)
from serdial21.modules.catalog.adapters.outbound.persistence.models import (
    ProductionCatalogModel,
    ProductionCatalogVersionModel,
)
from serdial21.modules.workflow.adapters.outbound.persistence.journeys import (
    JourneyCheckpointModel,
)


PREVIOUS = '20260908_0012'
HEAD = '20260916_0013'
LAB_DATABASE = 'u621451815_serdial21_mig'
pytestmark = pytest.mark.mariadb_migration


def _revision(engine: object) -> str:
    with engine.connect() as connection:  # type: ignore[attr-defined]
        return str(connection.scalar(text('SELECT version_num FROM alembic_version')))


def _assert_schema(engine: object) -> None:
    inspector = inspect(engine)
    assert inspector.get_table_options('document_metadata').get('mysql_engine') == 'InnoDB'

    bank_columns = {item['name']: item for item in inspector.get_columns('bank_accounts')}
    assert {'bank_name', 'nickname', 'status', 'updated_at'} <= bank_columns.keys()
    assert bank_columns['status']['nullable'] is False

    metadata_columns = {item['name']: item for item in inspector.get_columns('document_metadata')}
    assert {
        'id', 'tenant_id', 'company_id', 'receipt_id', 'document_number',
        'description', 'observation', 'version', 'created_at', 'updated_at',
    } == metadata_columns.keys()
    assert metadata_columns['version']['nullable'] is False
    assert metadata_columns['updated_at']['nullable'] is False

    journey_columns = {item['name']: item for item in inspector.get_columns('nfe_journey_checkpoints')}
    assert {'account_search', 'rule_search', 'source_search', 'accounting_date_index'} <= journey_columns.keys()

    bank_indexes = {item['name'] for item in inspector.get_indexes('bank_accounts')}
    metadata_indexes = {item['name'] for item in inspector.get_indexes('document_metadata')}
    journey_indexes = {item['name'] for item in inspector.get_indexes('nfe_journey_checkpoints')}
    assert 'ix_bank_accounts_scope_status' in bank_indexes
    assert {'ix_document_metadata_number', 'uq_document_metadata_receipt'} <= metadata_indexes
    assert 'ix_nfe_journey_search_date' in journey_indexes

    foreign_keys = {item['name']: item for item in inspector.get_foreign_keys('document_metadata')}
    assert foreign_keys['fk_document_metadata_receipt']['referred_table'] == 'artifact_receipts'
    assert foreign_keys['fk_document_metadata_receipt']['constrained_columns'] == [
        'tenant_id', 'company_id', 'receipt_id',
    ]
    assert foreign_keys['fk_document_metadata_receipt']['referred_columns'] == [
        'tenant_id', 'company_id', 'id',
    ]


def _assert_downgraded(engine: object) -> None:
    inspector = inspect(engine)
    assert 'document_metadata' not in inspector.get_table_names()
    bank_columns = {item['name'] for item in inspector.get_columns('bank_accounts')}
    journey_columns = {item['name'] for item in inspector.get_columns('nfe_journey_checkpoints')}
    assert {'bank_name', 'nickname', 'status', 'updated_at'}.isdisjoint(bank_columns)
    assert {'account_search', 'rule_search', 'source_search', 'accounting_date_index'}.isdisjoint(journey_columns)


def test_migration_0013_upgrade_backfill_downgrade_and_reupgrade(
    migration_engine: object,
) -> None:
    lab_url = dotenv_values('.env.mariadb-migration-lab').get('MARIADB_MIGRATION_DATABASE_URL')
    assert lab_url
    original_url = os.environ.get('DATABASE_URL')
    tenant_id, company_id, user_id, catalog_id = (uuid4() for _ in range(4))
    catalog_version_id, journey_row_id, journey_id = (uuid4() for _ in range(3))
    rule_id, account_id = uuid4(), uuid4()
    now = datetime(2026, 9, 16, 15, 0, tzinfo=UTC)
    snapshot = {
        'lines': [{'account_version_id': str(account_id)}],
        'plan': {'accounts': [{
            'id': str(account_id), 'code': '1.1.01', 'name': 'Caixa Homologação',
        }]},
        'evaluation': {'proposal': {'rule_version_id': str(rule_id)}},
        'sources': [{'source_type': 'FiscalDocument'}],
        'revision': {'accounting_date': '2026-09-16'},
    }
    catalog_content = {'rules': [{
        'id': str(rule_id), 'name': 'Regra Histórica Homologação',
    }]}

    try:
        os.environ['DATABASE_URL'] = lab_url
        config = Config('alembic.ini')
        command.upgrade(config, HEAD)
        assert _revision(migration_engine) == HEAD
        command.downgrade(config, PREVIOUS)
        assert _revision(migration_engine) == PREVIOUS
        _assert_downgraded(migration_engine)

        with migration_engine.begin() as connection:  # type: ignore[attr-defined]
            assert connection.scalar(text('SELECT DATABASE()')) == LAB_DATABASE
            connection.execute(TenantModel.__table__.insert().values(
                id=tenant_id, name='Tenant Migration 0013', timezone='UTC',
                currency_code='BRL', status='active', activated_at=now,
            ))
            connection.execute(UserModel.__table__.insert().values(
                id=user_id, provider_issuer='urn:serdial21:migration-0013',
                provider_subject=str(user_id), display_name='Migration 0013',
                is_active=True,
            ))
            connection.execute(CompanyModel.__table__.insert().values(
                id=company_id, tenant_id=tenant_id, legal_name='Company Migration 0013',
                tax_identifier=str(company_id.int)[:14], timezone='UTC',
                currency_code='BRL', status='active', valid_from=now,
            ))
            connection.execute(ProductionCatalogModel.__table__.insert().values(
                id=catalog_id, tenant_id=tenant_id, company_id=company_id,
                name='Catalog Migration 0013',
            ))
            connection.execute(ProductionCatalogVersionModel.__table__.insert().values(
                id=catalog_version_id, tenant_id=tenant_id, company_id=company_id,
                catalog_id=catalog_id, version_no=1, status='DRAFT',
                valid_from=date(2026, 9, 16), content=catalog_content,
                content_hash='0' * 64, created_by=user_id, created_at=now,
            ))
            connection.execute(JourneyCheckpointModel.__table__.insert().values(
                id=journey_row_id, tenant_id=tenant_id, company_id=company_id,
                journey_id=journey_id, correlation_id=uuid4(),
                idempotency_key=f'migration-0013-{journey_id}', version=1,
                status='PENDING_APPROVAL', snapshot=snapshot,
                snapshot_hash='0' * 64, created_at=now,
            ))

        command.upgrade(config, HEAD)
        assert _revision(migration_engine) == HEAD
        _assert_schema(migration_engine)
        with migration_engine.connect() as connection:  # type: ignore[attr-defined]
            rule_search = connection.scalar(select(
                JourneyCheckpointModel.rule_search,
            ).where(JourneyCheckpointModel.id == journey_row_id))
            assert str(rule_id) in rule_search
            assert 'regra histórica homologação' in rule_search
            assert connection.scalar(select(JourneyCheckpointModel.id).where(
                JourneyCheckpointModel.rule_search.ilike(f'%{rule_id}%'),
            )) == journey_row_id
            assert connection.scalar(select(JourneyCheckpointModel.id).where(
                JourneyCheckpointModel.rule_search.ilike('%regra histórica homologação%'),
            )) == journey_row_id

        command.downgrade(config, PREVIOUS)
        assert _revision(migration_engine) == PREVIOUS
        _assert_downgraded(migration_engine)
        command.upgrade(config, HEAD)
        assert _revision(migration_engine) == HEAD
        _assert_schema(migration_engine)
    finally:
        if 'config' in locals():
            command.upgrade(config, HEAD)
        if _revision(migration_engine) == HEAD:
            with migration_engine.begin() as connection:  # type: ignore[attr-defined]
                connection.execute(delete(JourneyCheckpointModel).where(
                    JourneyCheckpointModel.id == journey_row_id,
                ))
                connection.execute(delete(ProductionCatalogVersionModel).where(
                    ProductionCatalogVersionModel.id == catalog_version_id,
                ))
                connection.execute(delete(ProductionCatalogModel).where(
                    ProductionCatalogModel.id == catalog_id,
                ))
                connection.execute(delete(CompanyModel).where(CompanyModel.id == company_id))
                connection.execute(delete(UserModel).where(UserModel.id == user_id))
                connection.execute(delete(TenantModel).where(TenantModel.id == tenant_id))
        if original_url is None:
            os.environ.pop('DATABASE_URL', None)
        else:
            os.environ['DATABASE_URL'] = original_url
