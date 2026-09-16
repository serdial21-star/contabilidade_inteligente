import json
from pathlib import Path
import sqlite3

import pytest
from sqlalchemy.engine import make_url

from serdial21.ops.recovery import (
    BackupError,
    _mysqldump_command,
    create_sqlite_backup,
    restore_sqlite_backup,
)


def synthetic_database(path: Path) -> None:
    with sqlite3.connect(path) as connection:
        connection.execute('CREATE TABLE evidence (id INTEGER PRIMARY KEY, value TEXT)')
        connection.executemany(
            'INSERT INTO evidence(value) VALUES (?)', [('alpha',), ('beta',)]
        )


def test_synthetic_backup_restore_checksum_and_data_validation(tmp_path: Path) -> None:
    source = tmp_path / 'synthetic-source.sqlite3'
    backup = tmp_path / 'synthetic-backup.sqlite3'
    restored = tmp_path / 'synthetic-restored.sqlite3'
    synthetic_database(source)

    metadata = create_sqlite_backup(source, backup)
    metadata_path = tmp_path / 'metadata.json'
    metadata.write(metadata_path)
    restore_sqlite_backup(backup, restored, expected_sha256=metadata.sha256)

    assert metadata.file_size_bytes > 0
    assert len(metadata.sha256) == 64
    assert json.loads(metadata_path.read_text(encoding='utf-8'))['tool_exit_status'] == 0
    with sqlite3.connect(restored) as connection:
        assert connection.execute('PRAGMA integrity_check').fetchone() == ('ok',)
        assert connection.execute('SELECT COUNT(*) FROM evidence').fetchone() == (2,)


def test_restore_rejects_corrupted_artifact_without_creating_target(tmp_path: Path) -> None:
    artifact = tmp_path / 'corrupt.sqlite3'
    target = tmp_path / 'target.sqlite3'
    artifact.write_bytes(b'not-a-database')

    with pytest.raises(BackupError, match='checksum'):
        restore_sqlite_backup(artifact, target, expected_sha256='0' * 64)

    assert not target.exists()


def test_backup_fails_safely_for_invalid_destination(tmp_path: Path) -> None:
    source = tmp_path / 'source.sqlite3'
    destination = tmp_path / 'existing.sqlite3'
    synthetic_database(source)
    destination.write_bytes(b'preserve-me')

    with pytest.raises(BackupError, match='must not exist'):
        create_sqlite_backup(source, destination)

    assert destination.read_bytes() == b'preserve-me'


def test_mysqldump_command_never_contains_password_or_url() -> None:
    url = make_url('mysql+pymysql://backup_user:synthetic-secret@db.invalid:3307/serdial21')

    command = _mysqldump_command(url, 'serdial21', 'mysqldump')
    rendered = ' '.join(command)

    assert 'synthetic-secret' not in rendered
    assert 'mysql+pymysql' not in rendered
    assert command[-1] == 'serdial21'
