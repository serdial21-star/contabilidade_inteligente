'''Observabilidade técnica sanitizada, independente da auditoria de negócio.'''

from collections.abc import Mapping
from datetime import UTC, datetime
import json
import logging
import re
from threading import Lock
from time import perf_counter

from serdial21.shared_kernel.correlation import get_correlation_id, get_request_id


_FORBIDDEN_KEYS = (
    'authorization', 'password', 'senha', 'token', 'secret', 'segredo',
    'api_key', 'cookie', 'xml', 'ofx', 'prompt', 'account_number', 'bank',
)
_SENSITIVE_VALUE = re.compile(
    r'(?i)(bearer\s+\S+|<\s*(?:nfe|ofx)\b|(?:password|token|secret|api[_-]?key)\s*[=:])'
)
_METRIC_LABELS: dict[str, frozenset[str]] = {
    'http_requests_total': frozenset({'method', 'route_template', 'status_class'}),
    'http_errors_total': frozenset({'error_class'}),
    'auth_failures_total': frozenset({'reason'}),
    'authorization_denials_total': frozenset({'reason'}),
    'rate_limit_exceeded_total': frozenset({'bucket'}),
    'rate_limit_backend_unavailable_total': frozenset({'bucket'}),
    'payload_too_large_total': frozenset({'source'}),
    'parser_rejection_total': frozenset({'source'}),
    'document_import_total': frozenset({'source', 'result'}),
    'accounting_proposal_total': frozenset({'result'}),
    'accounting_decision_total': frozenset({'decision'}),
    'account_lock_block_total': frozenset(),
    'audit_write_failure_total': frozenset(),
    'items_classified_total': frozenset(),
    'items_auto_classified_total': frozenset(),
    'items_review_required_total': frozenset(),
    'classification_conflict_total': frozenset(),
    'classification_corrected_total': frozenset(),
    'account_mapping_missing_total': frozenset(),
    # Métricas legadas mantidas para compatibilidade durante o piloto.
    'imports_total': frozenset(),
    'errors_total': frozenset(),
    'proposals_total': frozenset(),
    'approvals_total': frozenset(),
    'rejections_total': frozenset(),
    'pending_total': frozenset(),
    'exports_total': frozenset(),
    'retries_total': frozenset(),
    'reconciliations_total': frozenset(),
}
_HISTOGRAM_LABELS: dict[str, frozenset[str]] = {
    'http_request_duration_seconds': frozenset(
        {'method', 'route_template', 'status_class'}
    ),
    'document_processing_duration_seconds': frozenset({'source', 'result'}),
    'processing_duration_seconds': frozenset(),
}


class StructuredJsonFormatter(logging.Formatter):
    '''Formata somente o envelope técnico permitido como uma linha JSON.'''

    def __init__(self, *, service: str = 'serdial21', environment: str = 'unknown') -> None:
        super().__init__()
        self._service = service
        self._environment = environment

    def format(self, record: logging.LogRecord) -> str:
        payload = {
            'timestamp': datetime.now(UTC).isoformat(),
            'level': record.levelname,
            'service': self._service,
            'environment': self._environment,
            'logger': record.name,
            'event_name': getattr(record, 'event', record.getMessage()),
            'request_id': getattr(record, 'request_id', get_request_id()),
            'correlation_id': getattr(record, 'correlation_id', get_correlation_id()),
            'fields': _sanitize(getattr(record, 'fields', {})),
        }
        return json.dumps(
            payload, ensure_ascii=False, sort_keys=True, separators=(',', ':')
        )


def configure_technical_logging(
    level: str, *, service: str = 'serdial21', environment: str = 'unknown',
) -> None:
    '''Configura o logger da aplicação sem alterar o logger raiz do processo.'''
    logger = logging.getLogger('serdial21')
    logger.setLevel(level)
    logger.propagate = False
    for handler in logger.handlers:
        if getattr(handler, '_serdial21_structured', False):
            handler.setFormatter(
                StructuredJsonFormatter(service=service, environment=environment)
            )
            return
    handler = logging.StreamHandler()
    handler._serdial21_structured = True  # type: ignore[attr-defined]
    handler.setFormatter(
        StructuredJsonFormatter(service=service, environment=environment)
    )
    logger.addHandler(handler)


def technical_event(
    event: str, *, fields: Mapping[str, object] | None = None,
    level: int = logging.INFO,
) -> None:
    _event(logging.getLogger('serdial21.technical'), event, fields, level)


def security_event(
    event: str, *, fields: Mapping[str, object] | None = None,
) -> None:
    _event(logging.getLogger('serdial21.security'), event, fields, logging.WARNING)


def data_access_event(
    event: str, *, fields: Mapping[str, object] | None = None,
) -> None:
    _event(logging.getLogger('serdial21.data_access'), event, fields, logging.INFO)


def sanitized_error(error: BaseException) -> str:
    '''Não propaga mensagem de exceção, que pode conter dado ou segredo.'''
    return ''.join(
        character for character in type(error).__name__
        if character.isalnum() or character == '_'
    )[:80] or 'UnknownError'


def _event(
    logger: logging.Logger, event: str,
    fields: Mapping[str, object] | None, level: int,
) -> None:
    logger.log(level, event, extra={
        'event': event,
        'request_id': get_request_id(),
        'correlation_id': get_correlation_id(),
        'fields': _sanitize(fields or {}),
    })


def _sanitize(value: object) -> object:
    if isinstance(value, Mapping):
        return {
            str(key): _sanitize(item)
            for key, item in value.items()
            if not any(
                fragment in str(key).lower().replace('-', '_')
                for fragment in _FORBIDDEN_KEYS
            )
        }
    if isinstance(value, str):
        if _SENSITIVE_VALUE.search(value):
            return '[REDACTED]'
        return value[:256]
    if isinstance(value, (int, float, bool)) or value is None:
        return value
    return type(value).__name__


MetricKey = tuple[str, tuple[tuple[str, str], ...]]


class MetricsRegistry:
    '''Métricas locais com esquema fixo e labels de baixa cardinalidade.'''

    def __init__(self) -> None:
        self._lock = Lock()
        self._counters: dict[MetricKey, int] = {
            (name, ()): 0 for name, labels in _METRIC_LABELS.items() if not labels
        }
        self._histograms: dict[MetricKey, tuple[int, float]] = {
            (name, ()): (0, 0.0)
            for name, labels in _HISTOGRAM_LABELS.items() if not labels
        }

    def increment(
        self, name: str, labels: Mapping[str, str] | None = None,
    ) -> None:
        key = self._metric_key(name, labels, _METRIC_LABELS)
        with self._lock:
            self._counters[key] = self._counters.get(key, 0) + 1

    def observe(
        self, name: str, duration_seconds: float,
        labels: Mapping[str, str] | None = None,
    ) -> None:
        key = self._metric_key(name, labels, _HISTOGRAM_LABELS)
        with self._lock:
            count, total = self._histograms.get(key, (0, 0.0))
            self._histograms[key] = (count + 1, total + max(duration_seconds, 0.0))

    def observe_processing(self, duration_seconds: float) -> None:
        self.observe('processing_duration_seconds', duration_seconds)

    def record_http(
        self, *, method: str, route_template: str, status_code: int,
        duration_seconds: float,
    ) -> None:
        labels = {
            'method': method.upper()[:12],
            'route_template': route_template,
            'status_class': f'{status_code // 100}xx',
        }
        self.increment('http_requests_total', labels)
        self.observe('http_request_duration_seconds', duration_seconds, labels)
        if status_code >= 500:
            self.increment('http_errors_total', {'error_class': '5xx'})

    def snapshot(self) -> dict[str, int | float]:
        '''Compatibilidade para testes/diagnóstico local sem exportar labels.'''
        with self._lock:
            result: dict[str, int | float] = {}
            for (name, labels), value in self._counters.items():
                if not labels:
                    result[name] = value
            for (name, labels), (count, total) in self._histograms.items():
                if not labels:
                    stem = name.removesuffix('_seconds')
                    result[f'{stem}_count'] = count
                    result[name] = total
            return result

    def render_prometheus(self) -> str:
        '''Renderiza texto para endpoint operacional explicitamente protegido.'''
        with self._lock:
            lines: list[str] = []
            for (name, labels), value in sorted(self._counters.items()):
                lines.append(f'{name}{_render_labels(labels)} {value}')
            for (name, labels), (count, total) in sorted(self._histograms.items()):
                suffix = _render_labels(labels)
                lines.append(f'{name}_count{suffix} {count}')
                lines.append(f'{name}_sum{suffix} {total:.9f}')
            return '\n'.join(lines) + '\n'

    @staticmethod
    def _metric_key(
        name: str, labels: Mapping[str, str] | None,
        schema: Mapping[str, frozenset[str]],
    ) -> MetricKey:
        if name not in schema:
            raise ValueError('metric is not registered')
        normalized = dict(labels or {})
        if frozenset(normalized) != schema[name]:
            raise ValueError('metric labels do not match registered low-cardinality schema')
        if any(len(value) > 120 for value in normalized.values()):
            raise ValueError('metric label value is too long')
        return name, tuple(sorted(normalized.items()))


def _render_labels(labels: tuple[tuple[str, str], ...]) -> str:
    if not labels:
        return ''
    rendered = ','.join(
        f'{key}="{value.replace(chr(92), chr(92) * 2).replace(chr(34), chr(92) + chr(34))}"'
        for key, value in labels
    )
    return '{' + rendered + '}'


def processing_started() -> float:
    return perf_counter()
