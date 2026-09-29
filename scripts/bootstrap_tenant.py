'''Cria ou localiza o tenant; idempotente por nome e identificador aprovados.

Uso típico em banco local: DATABASE_URL=sqlite:///local_data/serdial21_local.db
Imprime somente o identificador opaco do tenant, para uso em --tenant-id.
'''

from __future__ import annotations

import argparse
import json
from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session

from serdial21.bootstrap.audit import AuditContext, audit_scope
from serdial21.bootstrap.database import create_database_engine, create_session_factory
from serdial21.bootstrap.model_registry import load_models
from serdial21.bootstrap.settings import AppSettings
from serdial21.modules.access_control.adapters.outbound.persistence.models import TenantModel
from serdial21.modules.audit.domain.entities import AuditOrigin


def _find_or_prepare_tenant(
    session: Session,
    *,
    name: str,
    tenant_id: UUID | None,
    timezone: str,
    currency: str,
) -> tuple[TenantModel, bool]:
    by_name = session.scalars(select(TenantModel).where(TenantModel.name == name)).all()
    if len(by_name) > 1:
        raise SystemExit('mais de um tenant com esse nome; use o identificador diretamente')

    by_id = session.get(TenantModel, tenant_id) if tenant_id is not None else None
    if by_name:
        existing = by_name[0]
        if tenant_id is not None and existing.id != tenant_id:
            raise SystemExit('tenant existente com esse nome possui identificador diferente')
        return existing, False
    if by_id is not None:
        raise SystemExit('identificador de tenant já pertence a outro nome')

    tenant = TenantModel(
        id=tenant_id or uuid4(), name=name, timezone=timezone,
        currency_code=currency, status='active',
    )
    session.add(tenant)
    return tenant, True


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--name', required=True)
    parser.add_argument(
        '--tenant-id', type=UUID, default=None,
        help='identificador aprovado; se omitido, gera UUID somente para uso local',
    )
    parser.add_argument('--timezone', default='America/Sao_Paulo')
    parser.add_argument('--currency', default='BRL')
    args = parser.parse_args()

    load_models()
    session = create_session_factory(create_database_engine(AppSettings()))()
    try:
        tenant, created = _find_or_prepare_tenant(
            session,
            name=args.name,
            tenant_id=args.tenant_id,
            timezone=args.timezone,
            currency=args.currency,
        )
        if created:
            context = AuditContext(
                correlation_id=uuid4(), origin=AuditOrigin.HUMAN,
                reason='Criação manual de tenant por operador (bootstrap local)',
            )
            with audit_scope(session, context):
                session.commit()
        tenant_id = tenant.id
    except BaseException:
        session.rollback()
        raise
    finally:
        session.close()
    print(json.dumps({'tenant_id': str(tenant_id), 'created': created}))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
