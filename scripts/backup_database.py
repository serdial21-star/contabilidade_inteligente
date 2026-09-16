'''CLI de backup lógico; não executa restore nem sobrescreve artefatos.'''

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

from serdial21.bootstrap.settings import AppSettings
from serdial21.ops.recovery import BackupError, create_mysql_logical_backup


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('--expected-database', required=True)
    parser.add_argument('--output', required=True, type=Path)
    parser.add_argument('--mysqldump', default='mysqldump')
    args = parser.parse_args()
    try:
        metadata = create_mysql_logical_backup(
            AppSettings(), args.expected_database, args.output,
            executable=args.mysqldump,
        )
        metadata_path = args.output.with_suffix(args.output.suffix + '.metadata.json')
        metadata.write(metadata_path)
        print(json.dumps({'event_name': 'backup.completed', 'metadata': str(metadata_path)}))
        return 0
    except (BackupError, OSError, ValueError):
        print(json.dumps({'event_name': 'backup.failed', 'error': 'safe_failure'}), file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
