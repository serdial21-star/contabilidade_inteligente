'''Import manual, offline e idempotente de empresas do Sistema A (ADR 0013).

Não conecta ao banco do Sistema A. O operador exporta a tabela `clientes`
(phpMyAdmin -> Exportar -> CSV) e informa o arquivo aqui. Nunca lê a coluna
`senha` mesmo que ela exista no arquivo exportado.
'''

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from datetime import UTC, datetime
from uuid import UUID, uuid4

from serdial21.bootstrap.audit import AuditContext, audit_scope
from serdial21.bootstrap.database import create_database_engine, create_session_factory
from serdial21.bootstrap.model_registry import load_models
from serdial21.bootstrap.settings import AppSettings
from serdial21.modules.access_control.adapters.outbound.persistence.repositories import (
    SqlAlchemyCompanyImportRepository,
)
from serdial21.modules.access_control.application.services.company_import import (
    ExternalClientRecord,
    ImportExternalCompanies,
    clean_external_cell,
)
from serdial21.modules.audit.domain.entities import AuditOrigin


REQUIRED_COLUMNS = ('id', 'nome_cliente', 'status')


def _read_records(path: Path) -> list[ExternalClientRecord]:
    with path.open(newline='', encoding='utf-8-sig') as handle:
        reader = csv.DictReader(handle)
        missing = [column for column in REQUIRED_COLUMNS if column not in (reader.fieldnames or [])]
        if missing:
            raise ValueError(f'colunas obrigatórias ausentes no CSV: {", ".join(missing)}')
        records = []
        for row in reader:
            records.append(ExternalClientRecord(
                external_id=str(row['id']).strip(),
                nome_cliente=row['nome_cliente'],
                nome_fantasia=clean_external_cell(row.get('nome_fantasia')),
                cnpj=clean_external_cell(row.get('cnpj')),
                cnpj_cpf=clean_external_cell(row.get('cnpj_cpf')),
                status=row['status'],
            ))
        return records


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input', required=True, type=Path, help='CSV exportado de `clientes`')
    parser.add_argument('--tenant-id', required=True, type=UUID)
    parser.add_argument('--actor-id', type=UUID, default=None)
    parser.add_argument(
        '--reason', default='Import manual Sistema A -> Sistema B (ADR 0013)',
    )
    parser.add_argument('--dry-run', action='store_true',
                        help='executa tudo, mostra o relatório e desfaz (rollback)')
    args = parser.parse_args()

    records = _read_records(args.input)

    settings = AppSettings()
    engine = create_database_engine(settings)
    load_models()
    session = create_session_factory(engine)()
    try:
        context = AuditContext(
            correlation_id=uuid4(),
            origin=AuditOrigin.IMPORT,
            actor_id=args.actor_id,
            reason=args.reason,
        )
        with audit_scope(session, context):
            service = ImportExternalCompanies(SqlAlchemyCompanyImportRepository(session))
            report = service.execute(args.tenant_id, records, now=datetime.now(UTC))
            if args.dry_run:
                session.rollback()
            else:
                session.commit()
    except BaseException:
        session.rollback()
        raise
    finally:
        session.close()

    print(json.dumps({
        'event_name': 'sistema_a_company_import.completed',
        'dry_run': args.dry_run,
        'total_rows': len(records),
        'created': len(report.created),
        'unchanged': len(report.unchanged),
        'conflicts': [
            {'external_id': item.external_id, 'reason': item.reason} for item in report.conflicts
        ],
        'skipped': [
            {'external_id': item.external_id, 'reason': item.reason} for item in report.skipped
        ],
    }, ensure_ascii=False, indent=2))
    return 0 if not report.conflicts else 1


if __name__ == '__main__':
    raise SystemExit(main())
