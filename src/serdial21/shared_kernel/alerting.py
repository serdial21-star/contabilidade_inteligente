'''Porta neutra e despacho resiliente de alertas operacionais.'''

from collections.abc import Callable
from dataclasses import dataclass
from enum import StrEnum
from threading import Lock
from time import monotonic
from typing import Protocol

from serdial21.shared_kernel.observability import sanitized_error, technical_event


class AlertSeverity(StrEnum):
    INFO = 'INFO'
    WARNING = 'WARNING'
    CRITICAL = 'CRITICAL'


@dataclass(frozen=True)
class OperationalAlert:
    key: str
    category: str
    severity: AlertSeverity
    event_name: str
    runbook: str


class AlertSink(Protocol):
    def send(self, alert: OperationalAlert) -> None: ...


class NullAlertSink:
    '''Adapter padrão: interface pronta, sem transporte externo configurado.'''

    def send(self, alert: OperationalAlert) -> None:
        del alert


class InMemoryAlertSink:
    '''Fake determinístico para testes, sem rede.'''

    def __init__(self) -> None:
        self.alerts: list[OperationalAlert] = []

    def send(self, alert: OperationalAlert) -> None:
        self.alerts.append(alert)


class AlertDispatcher:
    '''Entrega best-effort com cooldown; falha não interrompe a aplicação.'''

    def __init__(
        self, sink: AlertSink, *, cooldown_seconds: float = 300,
        clock: Callable[[], float] = monotonic,
    ) -> None:
        if cooldown_seconds < 0:
            raise ValueError('cooldown_seconds must not be negative')
        self._sink = sink
        self._cooldown_seconds = cooldown_seconds
        self._clock = clock
        self._last_sent: dict[str, float] = {}
        self._lock = Lock()

    def emit(self, alert: OperationalAlert) -> bool:
        now = self._clock()
        with self._lock:
            last_sent = self._last_sent.get(alert.key)
            if last_sent is not None and now - last_sent < self._cooldown_seconds:
                return False
            # Reserva a janela antes do I/O para impedir tempestade concorrente.
            self._last_sent[alert.key] = now
        try:
            self._sink.send(alert)
        except Exception as error:
            technical_event(
                'alert.transport.failed',
                fields={
                    'category': alert.category,
                    'severity': alert.severity.value,
                    'error_type': sanitized_error(error),
                },
            )
            return False
        technical_event(
            'alert.dispatched',
            fields={'category': alert.category, 'severity': alert.severity.value},
        )
        return True
