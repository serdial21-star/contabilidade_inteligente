'''Ciclo focado da migration 0014 no Migration Lab isolado.'''
import os

import pytest
from alembic import command
from alembic.config import Config
from dotenv import dotenv_values
from sqlalchemy import inspect, text


pytestmark = pytest.mark.mariadb_migration
HEAD = '20260916_0014'
PREVIOUS = '20260916_0013'


def test_accounting_automation_migration_cycle(migration_engine: object) -> None:
    url = dotenv_values('.env.mariadb-migration-lab').get('MARIADB_MIGRATION_DATABASE_URL')
    assert url
    previous_url = os.environ.get('DATABASE_URL')
    config = Config('alembic.ini')
    try:
        os.environ['DATABASE_URL'] = url
        command.upgrade(config, HEAD)
        _assert_head(migration_engine, HEAD)
        _assert_schema(migration_engine)
        command.downgrade(config, PREVIOUS)
        _assert_head(migration_engine, PREVIOUS)
        assert 'item_classifications' not in inspect(migration_engine).get_table_names()
        command.upgrade(config, HEAD)
        _assert_head(migration_engine, HEAD)
        _assert_schema(migration_engine)
    finally:
        command.upgrade(config, HEAD)
        if previous_url is None:
            os.environ.pop('DATABASE_URL', None)
        else:
            os.environ['DATABASE_URL'] = previous_url


def _assert_head(engine: object, revision: str) -> None:
    with engine.connect() as connection:  # type: ignore[attr-defined]
        assert connection.scalar(text('SELECT DATABASE()')) == 'u621451815_serdial21_mig'
        assert connection.scalar(text('SELECT version_num FROM alembic_version')) == revision


def _assert_schema(engine: object) -> None:
    inspector = inspect(engine)
    expected = {'company_business_activities', 'company_accounting_profiles',
                'counterparties', 'company_item_profiles', 'item_classifications',
                'classification_evidence', 'classification_feedback'}
    assert expected <= set(inspector.get_table_names())
    fiscal_columns = {column['name'] for column in inspector.get_columns('fiscal_document_items')}
    assert {'gtin', 'cest', 'freight_total'} <= fiscal_columns
    assert 'ix_fiscal_items_product_identity' in {
        index['name'] for index in inspector.get_indexes('fiscal_document_items')
    }
    classification_fks = {fk['name'] for fk in inspector.get_foreign_keys('item_classifications')}
    assert 'fk_item_classifications_fiscal_item' in classification_fks
    feedback_fks = {fk['name'] for fk in inspector.get_foreign_keys('classification_feedback')}
    assert {'fk_classification_feedback_result', 'fk_classification_feedback_actor'} <= feedback_fks
