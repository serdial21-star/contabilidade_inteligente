'''Drill local exclusivamente para uma base SQLite sintética informada.'''

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sqlite3

from serdial21.ops.recovery import create_sqlite_backup, restore_sqlite_backup


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('--synthetic-source', required=True, type=Path)
    parser.add_argument('--backup', required=True, type=Path)
    parser.add_argument('--restore-target', required=True, type=Path)
    args = parser.parse_args()
    metadata = create_sqlite_backup(args.synthetic_source, args.backup)
    restore_sqlite_backup(
        args.backup, args.restore_target, expected_sha256=metadata.sha256
    )
    with sqlite3.connect(args.restore_target) as restored:
        integrity = restored.execute('PRAGMA integrity_check').fetchone()
    print(json.dumps({
        'event_name': 'recovery.drill.completed',
        'result': 'pass' if integrity == ('ok',) else 'fail',
        'sha256': metadata.sha256,
        'duration_seconds': metadata.duration_seconds,
    }))
    return 0 if integrity == ('ok',) else 1


if __name__ == '__main__':
    raise SystemExit(main())
