import pytest
from sqlalchemy import text


@pytest.mark.mariadb_runtime
def test_runtime_account_lock_incident_forensics(runtime_engine: object) -> None:
    with runtime_engine.connect() as connection:  # type: ignore[attr-defined]
        assert connection.scalar(text('SELECT DATABASE()')) == 'u621451815_serdial21_hom'
        assert connection.scalar(text('SELECT version_num FROM alembic_version')) == '20260907_0009'
        tables = set(connection.execute(text('SHOW TABLES')).scalars())
        assert {'account_locks', 'audit_events'} <= tables
        locks = connection.scalar(text('SELECT COUNT(*) FROM account_locks'))
        audits = connection.scalar(text('SELECT COUNT(*) FROM audit_events'))
        events = connection.scalar(text("SELECT COUNT(*) FROM audit_events WHERE module='locks'"))
        print(f'ACCOUNT_LOCKS={locks}; AUDIT_EVENTS={audits}; LOCK_AUDIT_EVENTS={events}')
