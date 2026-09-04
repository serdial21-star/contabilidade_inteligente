'''Criação, consulta e verificação dos eventos de auditoria.'''

from collections.abc import Callable, Mapping
from dataclasses import asdict, dataclass, replace
from datetime import UTC, datetime
from hashlib import sha256
import hmac
import json
from typing import Any
from uuid import UUID, uuid4

from serdial21.modules.audit.application.ports.repository import AuditRepository
from serdial21.modules.audit.domain.entities import AuditEvent, AuditOrigin


PROHIBITED_KEY_FRAGMENTS = (
    'password',
    'senha',
    'token',
    'secret',
    'segredo',
    'credential',
    'authorization',
    'api_key',
    'apikey',
    'xml',
    'raw_document',
    'document_content',
    'prompt',
)
MAX_AUDIT_STATE_BYTES = 16_384


class SensitiveAuditDataError(ValueError):
    '''Recusa payload que possa copiar segredo ou documento bruto.'''


@dataclass(frozen=True, slots=True)
class AuditRecord:
    tenant_id: UUID
    company_id: UUID | None
    actor_id: UUID | None
    origin: AuditOrigin
    module: str
    action: str
    subject_type: str
    subject_id: UUID
    subject_version: int | None
    before: Mapping[str, object] | None
    after: Mapping[str, object] | None
    reason: str | None
    correlation_id: UUID
    causation_id: UUID | None = None


class AuditService:
    '''Única fachada de escrita e leitura inicial da trilha.'''

    def __init__(
        self,
        repository: AuditRepository,
        *,
        id_factory: Callable[[], UUID] = uuid4,
        clock: Callable[[], datetime] | None = None,
    ) -> None:
        self._repository = repository
        self._id_factory = id_factory
        self._clock = clock or (lambda: datetime.now(UTC))

    def record(self, record: AuditRecord) -> AuditEvent:
        occurred_at = self._clock()
        if occurred_at.tzinfo is None or occurred_at.utcoffset() is None:
            raise ValueError('timestamp de auditoria deve possuir timezone')
        if not record.module.strip() or not record.action.strip():
            raise ValueError('módulo e ação de auditoria são obrigatórios')
        if not record.subject_type.strip():
            raise ValueError('tipo do objeto auditado é obrigatório')
        if record.reason is not None and len(record.reason) > 500:
            raise ValueError('motivo de auditoria excede 500 caracteres')

        event = AuditEvent(
            id=self._id_factory(),
            tenant_id=record.tenant_id,
            company_id=record.company_id,
            actor_id=record.actor_id,
            origin=record.origin,
            module=record.module,
            action=record.action,
            subject_type=record.subject_type,
            subject_id=record.subject_id,
            subject_version=record.subject_version,
            before=_normalize_state(record.before),
            after=_normalize_state(record.after),
            reason=record.reason,
            correlation_id=record.correlation_id,
            causation_id=record.causation_id,
            occurred_at=occurred_at.astimezone(UTC),
            integrity_hash='',
        )
        event = replace(event, integrity_hash=calculate_integrity_hash(event))
        self._repository.append(event)
        return event

    def get(self, tenant_id: UUID, event_id: UUID) -> AuditEvent | None:
        return self._repository.get(tenant_id, event_id)

    def list_by_correlation(
        self,
        tenant_id: UUID,
        correlation_id: UUID,
    ) -> list[AuditEvent]:
        return self._repository.list_by_correlation(tenant_id, correlation_id)

    @staticmethod
    def verify_integrity(event: AuditEvent) -> bool:
        expected = calculate_integrity_hash(event)
        return hmac.compare_digest(event.integrity_hash, expected)


def calculate_integrity_hash(event: AuditEvent) -> str:
    payload = asdict(event)
    payload.pop('integrity_hash', None)
    canonical = json.dumps(
        _json_value(payload),
        ensure_ascii=False,
        sort_keys=True,
        separators=(',', ':'),
    ).encode('utf-8')
    return sha256(canonical).hexdigest()


def _normalize_state(
    state: Mapping[str, object] | None,
) -> dict[str, Any] | None:
    if state is None:
        return None
    normalized = _json_value(dict(state))
    encoded = json.dumps(
        normalized,
        ensure_ascii=False,
        sort_keys=True,
        separators=(',', ':'),
    ).encode('utf-8')
    if len(encoded) > MAX_AUDIT_STATE_BYTES:
        raise SensitiveAuditDataError('estado de auditoria excede limite seguro')
    return normalized


def _json_value(value: object) -> Any:
    if isinstance(value, Mapping):
        result: dict[str, Any] = {}
        for raw_key, item in value.items():
            key = str(raw_key)
            normalized_key = key.lower().replace('-', '_')
            if any(part in normalized_key for part in PROHIBITED_KEY_FRAGMENTS):
                raise SensitiveAuditDataError(
                    f'campo proibido no estado de auditoria: {key}'
                )
            result[key] = _json_value(item)
        return result
    if isinstance(value, (list, tuple)):
        return [_json_value(item) for item in value]
    if isinstance(value, UUID):
        return str(value)
    if isinstance(value, datetime):
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError('datetime auditado deve possuir timezone')
        return value.astimezone(UTC).isoformat()
    if isinstance(value, str):
        lowered = value.lstrip().lower()
        if lowered.startswith('<?xml') or lowered.startswith('<nfe'):
            raise SensitiveAuditDataError('XML bruto não pode constar na auditoria')
        return value
    if value is None or isinstance(value, (bool, int, float)):
        return value
    raise TypeError(f'tipo não suportado no estado de auditoria: {type(value).__name__}')
