import json
import logging

from serdial21.shared_kernel.observability import MetricsRegistry, StructuredJsonFormatter, sanitized_error


def test_structured_log_keeps_correlation_and_removes_sensitive_fields() -> None:
    record = logging.LogRecord('serdial21.technical', logging.INFO, __file__, 1, 'ignored', (), None)
    record.event = 'http.request.completed'
    record.correlation_id = 'correlation-1'
    record.fields = {
        'status': 500,
        'password': 'never-log',
        'document_xml': '<NFe>never-log</NFe>',
        'safe': 'retained',
    }

    payload = json.loads(StructuredJsonFormatter().format(record))

    assert payload['correlation_id'] == 'correlation-1'
    assert payload['fields'] == {'safe': 'retained', 'status': 500}
    assert 'never-log' not in json.dumps(payload)


def test_metrics_expose_only_aggregates_and_processing_time() -> None:
    metrics = MetricsRegistry()
    metrics.increment('imports_total')
    metrics.increment('reconciliations_total')
    metrics.observe_processing(0.125)

    snapshot = metrics.snapshot()

    assert snapshot['imports_total'] == snapshot['reconciliations_total'] == 1
    assert snapshot['processing_duration_count'] == 1
    assert snapshot['processing_duration_seconds'] == 0.125
    assert 'tenant_id' not in snapshot and 'company_id' not in snapshot


def test_error_is_logged_only_by_sanitized_type() -> None:
    error = ValueError('password=do-not-log <NFe>raw</NFe>')

    assert sanitized_error(error) == 'ValueError'
