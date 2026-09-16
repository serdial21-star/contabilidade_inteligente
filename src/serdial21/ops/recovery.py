'''Backup lógico seguro e recuperação local sintética.'''

from __future__ import annotations

from contextlib import closing
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from hashlib import sha256
import json
import os
from pathlib import Path
import sqlite3
import subprocess
from time import perf_counter

from sqlalchemy import text

from serdial21 import __version__
from serdial21.bootstrap.database import create_database_engine, normalized_database_url
from serdial21.bootstrap.settings import AppSettings


class BackupError(RuntimeError):
    '''Falha operacional sanitizada; detalhes do fornecedor não são propagados.'''


@dataclass(frozen=True)
class BackupMetadata:
    created_at: str
    backup_type: str
    database_class: str
    file_size_bytes: int
    sha256: str
    duration_seconds: float
    tool_exit_status: int
    application_version: str
    migration_head: str | None

    def write(self, destination: Path) -> None:
        try:
            with destination.open('x', encoding='utf-8') as output:
                output.write(json.dumps(asdict(self), indent=2, sort_keys=True) + '\n')
        except OSError as error:
            raise BackupError('backup metadata could not be written safely') from error


def file_sha256(path: Path) -> str:
    digest = sha256()
    with path.open('rb') as source:
        while chunk := source.read(1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def create_sqlite_backup(source: Path, destination: Path) -> BackupMetadata:
    '''Cria artefato novo a partir de uma base sintética/local somente leitura.'''
    source = source.resolve()
    destination = destination.resolve()
    _require_new_destination(source, destination)
    if not source.is_file():
        raise BackupError('backup source is unavailable')
    started = perf_counter()
    partial = destination.with_name(destination.name + '.partial')
    try:
        with closing(sqlite3.connect(f'{source.as_uri()}?mode=ro', uri=True)) as origin:
            with closing(sqlite3.connect(partial)) as target:
                origin.backup(target)
                if target.execute('PRAGMA integrity_check').fetchone() != ('ok',):
                    raise BackupError('backup integrity validation failed')
        partial.replace(destination)
    except Exception as error:
        partial.unlink(missing_ok=True)
        if isinstance(error, BackupError):
            raise
        raise BackupError('backup command failed safely') from error
    return _metadata(destination, 'sqlite_logical', perf_counter() - started, None)


def restore_sqlite_backup(
    artifact: Path, destination: Path, *, expected_sha256: str,
) -> None:
    '''Restaura somente em destino inexistente e valida integridade.'''
    artifact = artifact.resolve()
    destination = destination.resolve()
    _require_new_destination(artifact, destination)
    if not artifact.is_file() or file_sha256(artifact) != expected_sha256:
        raise BackupError('backup checksum validation failed')
    partial = destination.with_name(destination.name + '.partial')
    try:
        with closing(sqlite3.connect(f'{artifact.as_uri()}?mode=ro', uri=True)) as source:
            with closing(sqlite3.connect(partial)) as target:
                source.backup(target)
                if target.execute('PRAGMA integrity_check').fetchone() != ('ok',):
                    raise BackupError('restore integrity validation failed')
        partial.replace(destination)
    except Exception as error:
        partial.unlink(missing_ok=True)
        if isinstance(error, BackupError):
            raise
        raise BackupError('restore command failed safely') from error


def create_mysql_logical_backup(
    settings: AppSettings, expected_database: str, destination: Path,
    *, executable: str = 'mysqldump',
) -> BackupMetadata:
    '''Executa mysqldump após guard read-only de identidade do banco.'''
    url = normalized_database_url(settings)
    if url.get_backend_name() != 'mysql' or url.database != expected_database:
        raise BackupError('database guard rejected configured source')
    destination = destination.resolve()
    _require_new_destination(None, destination)
    engine = create_database_engine(settings)
    migration_head: str | None = None
    try:
        with engine.connect() as connection:
            if connection.scalar(text('SELECT DATABASE()')) != expected_database:
                raise BackupError('database guard rejected connected source')
            migration_head = connection.scalar(
                text('SELECT version_num FROM alembic_version')
            )
    except BackupError:
        raise
    except Exception as error:
        raise BackupError('database preflight failed safely') from error
    finally:
        engine.dispose()

    command = _mysqldump_command(url, expected_database, executable)
    environment = os.environ.copy()
    if url.password:
        environment['MYSQL_PWD'] = url.password
    partial = destination.with_name(destination.name + '.partial')
    started = perf_counter()
    try:
        with partial.open('xb') as output:
            result = subprocess.run(
                command,
                stdout=output,
                stderr=subprocess.PIPE,
                env=environment,
                check=False,
                timeout=3600,
            )
        if result.returncode != 0:
            raise BackupError('backup tool returned non-zero status')
        if partial.stat().st_size == 0:
            raise BackupError('backup artifact is empty')
        partial.replace(destination)
    except Exception as error:
        partial.unlink(missing_ok=True)
        if isinstance(error, BackupError):
            raise
        raise BackupError('backup command failed safely') from error
    finally:
        environment.pop('MYSQL_PWD', None)
    return _metadata(
        destination, 'mysql_logical', perf_counter() - started, migration_head
    )


def _mysqldump_command(url: object, database: str, executable: str) -> list[str]:
    host = getattr(url, 'host', None)
    username = getattr(url, 'username', None)
    port = getattr(url, 'port', None)
    if not host or not username or not database:
        raise BackupError('database connection metadata is incomplete')
    return [
        executable,
        '--single-transaction', '--quick', '--skip-lock-tables',
        '--no-tablespaces', '--default-character-set=utf8mb4', '--hex-blob',
        '--set-gtid-purged=OFF', '--column-statistics=0', '--triggers',
        '--add-drop-table', '--host', str(host), '--port', str(port or 3306),
        '--user', str(username), database,
    ]


def _metadata(
    path: Path, backup_type: str, duration: float, migration_head: str | None,
) -> BackupMetadata:
    return BackupMetadata(
        created_at=datetime.now(UTC).isoformat(),
        backup_type=backup_type,
        database_class='synthetic_local' if backup_type.startswith('sqlite') else 'configured_mysql',
        file_size_bytes=path.stat().st_size,
        sha256=file_sha256(path),
        duration_seconds=round(duration, 6),
        tool_exit_status=0,
        application_version=__version__,
        migration_head=migration_head,
    )


def _require_new_destination(source: Path | None, destination: Path) -> None:
    if source is not None and source == destination:
        raise BackupError('source and destination must differ')
    if destination.exists() or destination.with_name(destination.name + '.partial').exists():
        raise BackupError('destination must not exist')
    if not destination.parent.is_dir():
        raise BackupError('destination directory is unavailable')
