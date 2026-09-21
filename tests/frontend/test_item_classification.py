'''Focused static contracts for the item-classification review queue.'''

from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
APP = ROOT / 'app'


def source(name: str) -> str:
    return (APP / name).read_text(encoding='utf-8')


def test_api_client_exposes_item_classification_endpoints_without_idempotency_key() -> None:
    client = source('api-client.js')
    assert '/item-classifications?' in client
    assert '/item-classifications/${encodeURIComponent(id)}`)' in client
    assert '/item-classifications/${encodeURIComponent(id)}/decide' in client
    assert 'final_intent: decision.finalIntent' in client
    assert 'decision_type: decision.decisionType' in client
    assert 'apply_scope: decision.applyScope' in client


def test_accounting_service_exposes_full_item_classification_vocabulary() -> None:
    service = source('accounting-service.js')
    for status in (
        'REVIEW_REQUIRED', 'CONFLICTING_EVIDENCE', 'AUTO_CLASSIFIED',
        'PRE_CLASSIFIED', 'REVIEWED', 'PENDING_RULE', 'ACCOUNT_MAPPING_REQUIRED',
    ):
        assert status in service
    assert 'itemClassificationStatusLabel' in service
    assert 'ACCOUNTING_INTENTS' in service
    assert 'APPLY_SCOPE' in service
    assert 'UNCLASSIFIED' not in service.split('ACCOUNTING_INTENTS')[1].split('});')[0]


def test_app_wires_item_classification_queue_and_detail_routes() -> None:
    app = source('app.js')
    assert "href=\"#accounting?view=items\"" in app
    assert "routeParams().has('item')" in app
    assert "routeParams().get('view') === 'items'" in app
    assert 'accountingService.itemClassifications(companyId, itemQueueFilters)' in app
    assert 'accountingService.itemClassification(companyId, ' in app
    assert "data-action=\"open-item-classification\"" in app
    assert "data-action=\"item-queue-page\"" in app


def test_item_classification_detail_enforces_review_permission_before_deciding() -> None:
    app = source('app.js')
    assert "['REVIEW_REQUIRED', 'CONFLICTING_EVIDENCE'].includes(summary.status)" in app
    assert "hasPermission(currentPermissions(profile), ['accounting.classification.review'])" in app


def test_item_classification_rendering_escapes_untrusted_fields() -> None:
    app = source('app.js')
    assert 'escapeHtml(item.item_description)' in app
    assert 'escapeHtml(summary.item_description)' in app
    assert 'escapeHtml(item.explanation)' in app
    assert 'fetch(' not in app


def test_item_classification_decision_form_computes_decision_type_from_change() -> None:
    app = source('app.js')
    assert "id === 'item-classification-decision-form'" in app
    assert "finalIntent === detail.summary.selected_intent ? 'CONFIRMATION' : 'CORRECTION'" in app
    assert 'accountingService.decideItemClassification(companyId, detail.summary.id' in app


def test_company_and_logout_switches_reset_item_decision_state() -> None:
    app = source('app.js')
    assert "decisionIntent = null; decisionFeedback = null; itemDecisionOpen = false; itemDecisionFeedback = null;" in app
    assert 'itemQueueFilters = Object.freeze({...itemQueueFilters, offset: 0});' in app


def test_mock_provider_implements_item_classification_contract() -> None:
    mock = source('mock-provider.js')
    for member in ('itemClassifications:', 'itemClassification:', 'decideItemClassification:'):
        assert member in mock
    assert "syntheticItemClassificationStatus === 'REVIEWED'" in mock
