from serdial21.shared_kernel.alerting import (
    AlertDispatcher,
    AlertSeverity,
    InMemoryAlertSink,
    OperationalAlert,
)


def alert(severity: AlertSeverity = AlertSeverity.WARNING) -> OperationalAlert:
    return OperationalAlert(
        key='backup.failed',
        category='BACKUP',
        severity=severity,
        event_name='backup.failed',
        runbook='RECOVERY_RUNBOOK.md',
    )


def test_warning_and_critical_alerts_reach_provider_neutral_sink() -> None:
    sink = InMemoryAlertSink()
    dispatcher = AlertDispatcher(sink, cooldown_seconds=0)

    assert dispatcher.emit(alert()) is True
    assert dispatcher.emit(alert(AlertSeverity.CRITICAL)) is True
    assert [item.severity for item in sink.alerts] == [
        AlertSeverity.WARNING, AlertSeverity.CRITICAL,
    ]


def test_alerts_are_deduplicated_during_cooldown() -> None:
    sink = InMemoryAlertSink()
    dispatcher = AlertDispatcher(sink, cooldown_seconds=60, clock=lambda: 10)

    assert dispatcher.emit(alert()) is True
    assert dispatcher.emit(alert()) is False
    assert len(sink.alerts) == 1


def test_transport_failure_does_not_escape_dispatcher() -> None:
    class FailingSink:
        def send(self, _: OperationalAlert) -> None:
            raise RuntimeError('synthetic-secret-must-not-escape')

    assert AlertDispatcher(FailingSink()).emit(alert()) is False
