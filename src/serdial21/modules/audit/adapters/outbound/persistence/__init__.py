'''Persistência SQLAlchemy da auditoria.'''

from serdial21.modules.audit.adapters.outbound.persistence.repositories import (
    SqlAlchemyAuditRepository,
)

__all__ = ['SqlAlchemyAuditRepository']
