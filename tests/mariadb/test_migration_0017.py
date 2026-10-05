'''Ciclo focado da migration 0017 no Migration Lab isolado.'''
import os

import pytest
from alembic import command
from alembic.config import Config
from dotenv import dotenv_values
from sqlalchemy import inspect


pytestmark = pytest.mark.mariadb_migration
PREVIOUS = '20260923_0016'
TABLE = 'nfe_journey_document_reservations'


def test_journey_document_reservation_migration_cycle(migration_engine: object) -> None:
    url = dotenv_values('.env.mariadb-migration-lab').get('MARIADB_MIGRATION_DATABASE_URL')
    assert url
    previous_url = os.environ.get('DATABASE_URL')
    config = Config('alembic.ini')
    try:
        os.environ['DATABASE_URL'] = url
        command.upgrade(config, 'head')
        inspector = inspect(migration_engine)
        assert TABLE in inspector.get_table_names()
        uniques = {item['name'] for item in inspector.get_unique_constraints(TABLE)}
        assert 'uq_nfe_journey_document_active' in uniques
    fks = {item['name'] for item in inspector.get_foreign_keys(TABLE)}
    assert {'fk_nfe_journey_reservation_company', 'fk_nfe_journey_reservation_document'} <= fks
    columns = {item['name']: item for item in inspector.get_columns(TABLE)}
    assert columns['created_by']['nullable'] is True
        command.downgrade(config, PREVIOUS)
        assert TABLE not in inspect(migration_engine).get_table_names()
        command.upgrade(config, 'head')
    finally:
        command.upgrade(config, 'head')
        if previous_url is None:
            os.environ.pop('DATABASE_URL', None)
        else:
            os.environ['DATABASE_URL'] = previous_url
