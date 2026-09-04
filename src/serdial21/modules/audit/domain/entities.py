'''Entidades puras e enumerações da trilha de auditoria.'''

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from typing import Any
from uuid import UUID


class AuditOrigin(StrEnum):
    HUMAN = 'HUMAN'
    AI = 'AI'
    RULE_ENGINE = 'RULE_ENGINE'
    IMPORT = 'IMPORT'
    API = 'API'
    INTEGRATION = 'INTEGRATION'
    AUTOMATION = 'AUTOMATION'


class AuditEventImmutableError(RuntimeError):
    '''Impede alteração ou exclusão de um evento já persistido.'''


@dataclass(frozen=True, slots=True)
class AuditEvent:
    id: UUID
    tenant_id: UUID
    company_id: UUID | None
    actor_id: UUID | None
    origin: AuditOrigin
    module: str
    action: str
    subject_type: str
    subject_id: UUID
    subject_version: int | None
    before: dict[str, Any] | None
    after: dict[str, Any] | None
    reason: str | None
    correlation_id: UUID
    causation_id: UUID | None
    occurred_at: datetime
    integrity_hash: str

