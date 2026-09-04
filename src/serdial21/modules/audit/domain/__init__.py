'''Modelo de domínio da auditoria.'''

from serdial21.modules.audit.domain.entities import (
    AuditEvent,
    AuditEventImmutableError,
    AuditOrigin,
)

__all__ = ['AuditEvent', 'AuditEventImmutableError', 'AuditOrigin']

