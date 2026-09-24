'''Import manual, offline e idempotente da equipe interna do Sistema A (ADR 0013).

Não conecta ao banco do Sistema A. Exporte `funcionarios` (e, opcionalmente,
`clientes`) do phpMyAdmin para CSV. As colunas `senha`, `endereco`, `telefone`,
`contato_emergencia`, `observacao` e `matricula` nunca são lidas.
Ordem: rode antes `import_sistema_a_companies.py`; o vínculo empresa ->
responsável só cobre empresas já importadas.
'''

from __future__ import annotations

import argparse
import csv
from datetime import UTC, datetime
import json
from pathlib import Path
from uuid import UUID, uuid4

from serdial21.bootstrap.audit import AuditContext, audit_scope
from serdial21.bootstrap.database import create_database_engine, create_session_factory
from serdial21.bootstrap.model_registry import load_models
from serdial21.bootstrap.settings import AppSettings
from serdial21.modules.access_control.adapters.outbound.persistence.repositories import (
    SqlAlchemyTeamImportRepository,
)
from serdial21.modules.access_control.application.services.company_import import (
    clean_external_cell,
)
from serdial21.modules.access_control.application.services.team_import import (
    AssignResponsibleFromExternalClients,
    ExternalResponsibleRecord,
    ExternalStaffRecord,
    ImportExternalTeam,
)
from serdial21.modules.audit.domain.entities import AuditOrigin


def _rows(path: Path, required: tuple[str, ...]) -> list[dict[str, str]]:
    with path.open(newline='', encoding='utf-8-sig') as handle:
        reader = csv.DictReader(handle)
        missing = [name for name in required if name not in (reader.fieldnames or [])]
        if missing:
            raise ValueError(f'colunas obrigatórias ausentes em {path.name}: {", ".join(missing)}')
        return list(reader)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--funcionarios', required=True, type=Path)
    parser.add_argument('--clientes', type=Path, default=None,
                        help='CSV de `clientes`; habilita o vínculo empresa -> responsável')
    parser.add_argument('--tenant-id', required=True, type=UUID)
    parser.add_argument('--actor-id', type=UUID, default=None)
    parser.add_argument('--reason', default='Import manual equipe Sistema A -> Sistema B (ADR 0013)')
    parser.add_argument('--dry-run', action='store_true',
                        help='executa tudo, mostra o relatório e desfaz (rollback)')
    args = parser.parse_args()

    staff = [
        ExternalStaffRecord(
            external_id=str(row['id']).strip(), nome_funcionario=row['nome_funcionario'],
            email=clean_external_cell(row.get('email')), cargo=clean_external_cell(row.get('cargo')),
            status=row['status'],
        )
        for row in _rows(args.funcionarios, ('id', 'nome_funcionario', 'status'))
    ]
    responsibles = [
        ExternalResponsibleRecord(str(row['id']).strip(), clean_external_cell(row.get('responsavel')))
        for row in (_rows(args.clientes, ('id', 'responsavel')) if args.clientes else [])
    ]

    load_models()
    session = create_session_factory(create_database_engine(AppSettings()))()
    assignment = None
    try:
        context = AuditContext(
            correlation_id=uuid4(), origin=AuditOrigin.IMPORT,
            actor_id=args.actor_id, reason=args.reason,
        )
        with audit_scope(session, context):
            repository = SqlAlchemyTeamImportRepository(session)
            now = datetime.now(UTC)
            team = ImportExternalTeam(repository).execute(args.tenant_id, staff, now=now)
            if responsibles:
                assignment = AssignResponsibleFromExternalClients(repository).execute(
                    args.tenant_id, responsibles, now=now)
            if args.dry_run:
                session.rollback()
            else:
                session.commit()
    except BaseException:
        session.rollback()
        raise
    finally:
        session.close()

    summary: dict[str, object] = {
        'event_name': 'sistema_a_team_import.completed',
        'dry_run': args.dry_run,
        'team': {
            'total_rows': len(staff), 'created': len(team.created), 'unchanged': len(team.unchanged),
            'conflicts': [{'external_id': i.external_id, 'reason': i.reason} for i in team.conflicts],
            'skipped': [{'external_id': i.external_id, 'reason': i.reason} for i in team.skipped],
        },
    }
    if assignment is not None:
        summary['assignments'] = {
            'created': len(assignment.created), 'unchanged': len(assignment.unchanged),
            'without_responsible': len(assignment.without_responsible),
            'company_missing': list(assignment.company_missing),
            'unmatched': list(assignment.unmatched), 'ambiguous': list(assignment.ambiguous),
            'inactive_member': list(assignment.inactive_member),
        }
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 1 if team.conflicts else 0


if __name__ == '__main__':
    raise SystemExit(main())
