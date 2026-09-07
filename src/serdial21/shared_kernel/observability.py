'''Observabilidade técnica sanitizada, independente da auditoria de negócio.'''

from collections.abc import Mapping
from datetime import UTC, datetime
import json
import logging
from threading import Lock
from time import perf_counter
from typing import Any

from serdial21.shared_kernel.correlation import get_correlation_id


_FORBIDDEN = ('password', 'senha', 'token', 'secret', 'segredo', 'xml', 'prompt', 'account_number', 'bank')


class StructuredJsonFormatter(logging.Formatter):
    '''Formata somente o envelope técnico permitido como uma linha JSON.'''

    def format(self, record: logging.LogRecord) -> str:
        payload = {
            'timestamp': datetime.now(UTC).isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'event': getattr(record, 'event', record.getMessage()),
            'correlation_id': getattr(record, 'correlation_id', get_correlation_id()),
            'fields': _sanitize(getattr(record, 'fields', {})),
        }
        return json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(',', ':'))


def configure_technical_logging(level: str) -> None:
    '''Configura o logger da aplicação sem alterar o logger raiz do processo.'''
    logger = logging.getLogger('serdial21')
    logger.setLevel(level)
    logger.propagate = False
    if any(getattr(handler, '_serdial21_structured', False) for handler in logger.handlers):
        return
    handler = logging.StreamHandler()
    handler._serdial21_structured = True  # type: ignore[attr-defined]
    handler.setFormatter(StructuredJsonFormatter())
    logger.addHandler(handler)


def technical_event(event: str, *, fields: Mapping[str, object] | None = None, level: int = logging.INFO) -> None:
    _event(logging.getLogger('serdial21.technical'), event, fields, level)


def security_event(event: str, *, fields: Mapping[str, object] | None = None) -> None:
    _event(logging.getLogger('serdial21.security'), event, fields, logging.WARNING)


def data_access_event(event: str, *, fields: Mapping[str, object] | None = None) -> None:
    _event(logging.getLogger('serdial21.data_access'), event, fields, logging.INFO)


def sanitized_error(error: BaseException) -> str:
    '''Não propaga mensagem de exceção, que pode conter dado do usuário ou segredo.'''
    return ''.join(character for character in type(error).__name__ if character.isalnum() or character == '_')[:80] or 'UnknownError'


def _event(logger: logging.Logger, event: str, fields: Mapping[str, object] | None, level: int) -> None:
    logger.log(level, event, extra={
        'event': event,
        'correlation_id': get_correlation_id(),
        'fields': _sanitize(fields or {}),
    })


def _sanitize(value: object) -> object:
    if isinstance(value, Mapping):
        return {
            str(key): _sanitize(item)
            for key, item in value.items()
            if not any(fragment in str(key).lower().replace('-', '_') for fragment in _FORBIDDEN)
        }
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    return type(value).__name__


class MetricsRegistry:
    '''Contadores e tempos agregados locais, sem tenant, empresa ou conteúdo.'''

    def __init__(self) -> None:
        self._lock = Lock()
        self._counters: dict[str, int] = {
            'imports_total': 0, 'errors_total': 0, 'proposals_total': 0,
            'approvals_total': 0, 'rejections_total': 0, 'pending_total': 0,
            'exports_total': 0, 'retries_total': 0, 'reconciliations_total': 0,
            'processing_duration_count': 0,
        }
        self._processing_duration_seconds = 0.0

    def increment(self, name: str) -> None:
        with self._lock:
            self._counters.setdefault(name, 0)
            self._counters[name] += 1

    def observe_processing(self, duration_seconds: float) -> None:
        with self._lock:
            self._counters['processing_duration_count'] += 1
            self._processing_duration_seconds += max(duration_seconds, 0.0)

    def snapshot(self) -> dict[str, int | float]:
        with self._lock:
            return {**self._counters, 'processing_duration_seconds': self._processing_duration_seconds}


def processing_started() -> float:
    return perf_counter()
