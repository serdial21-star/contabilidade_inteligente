"""Contratos do contexto operacional configurável."""

from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
APP = ROOT / 'app'


def source(name: str) -> str:
    return (APP / name).read_text(encoding='utf-8')


def test_context_has_company_reference_month_and_startup_preference() -> None:
    app = source('app.js')
    for marker in (
        'Contexto de trabalho', 'Empresa e período', 'reference_month',
        'ask_at_start', 'Solicitar empresa e período sempre que eu entrar',
        'open-work-context', 'Contexto e preferências',
    ):
        assert marker in app


def test_review_expiry_policy_is_bounded_and_period_based() -> None:
    service = source('work-context.js')
    assert 'days >= 1 && days <= 90' in service
    assert 'day + sanitizeDays(reviewDays)' in service
    app = source('app.js')
    assert 'Dias para revisão' in app
    assert 'Data da importação' in app and 'Fim do período de referência' in app
    assert 'workContextService.reviewExpiry(workContext.periodEnd' in app


def test_saved_company_is_revalidated_against_authorized_context() -> None:
    service = source('work-context.js')
    assert 'authorizedIds.has(saved.companyId)' in service
    assert "throw new Error('unauthorized company context')" in service
    assert 'Nenhum XML, valor ou credencial é armazenado.' in source('app.js')
