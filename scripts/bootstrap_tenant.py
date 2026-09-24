'''Cria (ou localiza) o tenant do escritório; idempotente por nome exato.

Uso típico em banco local: DATABASE_URL=sqlite:///local_data/serdial21_local.db
Imprime somente o identificador opaco do tenant, para uso em --tenant-id.
'''

from __future__ import annotations

import argparse
import json
from uuid import uuid4

from sqlalchemy import select

from serdial21.bootstrap.audit import AuditContext, audit_scope
from serdial21.bootstrap.database import create_database_engine, create_session_factory
from serdial21.bootstrap.model_registry import load_models
from serdial21.bootstrap.settings import AppSettings
from serdial21.modules.access_control.adapters.outbound.persistence.models import TenantModel
from serdial21.modules.audit.domain.entities import AuditOrigin


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--name', required=True)
    parser.add_argument('--timezone', default='America/Sao_Paulo')
    parser.add_argument('--currency', default='BRL')
    args = parser.parse_args()

    load_models()
    session = create_session_factory(create_database_engine(AppSettings()))()
    try:
        existing = session.scalars(select(TenantModel).where(TenantModel.name == args.name)).all()
        if len(existing) > 1:
            raise SystemExit('mais de um tenant com esse nome; use o identificador diretamente')
        if existing:
            tenant_id, created = existing[0].id, False
        else:
            tenant = TenantModel(
                id=uuid4(), name=args.name, timezone=args.timezone,
                currency_code=args.currency, status='active',
            )
            context = AuditContext(
                correlation_id=uuid4(), origin=AuditOrigin.HUMAN,
                reason='Criação manual de tenant por operador (bootstrap local)',
            )
            with audit_scope(session, context):
                session.add(tenant)
                session.commit()
            tenant_id, created = tenant.id, True
    except BaseException:
        session.rollback()
        raise
    finally:
        session.close()
    print(json.dumps({'tenant_id': str(tenant_id), 'created': created}))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
