import pytest
from sqlalchemy import text


@pytest.mark.mariadb_migration
def test_migration_lab_is_distinct_and_mariadb_11_8(migration_engine: object) -> None:
    with migration_engine.connect() as connection:  # type: ignore[attr-defined]
        version = str(connection.scalar(text('SELECT VERSION()')))
        assert version.startswith('11.8.') and 'MariaDB' in version
        assert connection.scalar(text('SELECT DATABASE()')) != 'u621451815_serdial21_hom'
