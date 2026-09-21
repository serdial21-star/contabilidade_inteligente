from pathlib import Path

from serdial21.shared_kernel.observability import (
    _HISTOGRAM_LABELS,
    _METRIC_LABELS,
)


ROOT = Path(__file__).resolve().parents[2]


def read(relative: str) -> str:
    return (ROOT / relative).read_text(encoding="utf-8")


def test_phase13_required_documents_and_human_gates_are_explicit() -> None:
    required = (
        "docs/privacy/DATA_INVENTORY.md",
        "docs/privacy/DATA_FLOW_MAP.md",
        "docs/privacy/PRIVACY_ROLE_MATRIX.md",
        "docs/privacy/LAWFUL_BASIS_REVIEW_MATRIX.md",
        "docs/privacy/RETENTION_POLICY_TECHNICAL.md",
        "docs/privacy/PRIVACY_INCIDENT_PLAYBOOK.md",
        "docs/privacy/SUBPROCESSOR_TECHNICAL_REGISTER.md",
        "docs/privacy/ROPA_TECHNICAL_INPUT.md",
        "docs/privacy/PRIVACY_RISK_REGISTER.md",
        "docs/privacy/RIPD_TECHNICAL_INPUT.md",
        "docs/legal/PRIVACY_NOTICE_TECHNICAL_INPUT.md",
        "docs/legal/SAAS_CONTRACT_TECHNICAL_INPUT.md",
        "docs/legal/DPA_TECHNICAL_INPUT.md",
        "docs/legal/INFORMATION_SECURITY_ANNEX_DRAFT.md",
        "docs/legal/LGPD_LEGAL_REVIEW_CHECKLIST.md",
    )
    contents = "\n".join(read(path) for path in required)
    assert all((ROOT / path).is_file() for path in required)
    assert "LEGAL_REVIEW_REQUIRED" in contents
    assert "PENDING_HUMAN" in contents

    assessment = read("docs/privacy/PHASE_13_TECHNICAL_ASSESSMENT.md")
    for gate in (
        "`TECHNICAL_PRIVACY_GATE` | `PASS`",
        "`LEGAL_REVIEW_GATE` | `PENDING`",
        "`CONTRACTUAL_GATE` | `PENDING`",
        "`REAL_DATA` | `NO_GO`",
        "`APPLICATION_EXTERNAL_EXPOSURE` | `NO_GO`",
        "`MIGRATION_0012` | `PRE_DEPLOY_REQUIRED`",
    ):
        assert gate in assessment


def test_restore_and_incident_evidence_fail_closed() -> None:
    backup = read("docs/BACKUP_RECOVERY_STRATEGY.md")
    recovery = read("docs/RECOVERY_RUNBOOK.md")
    incident = read("docs/privacy/PRIVACY_INCIDENT_PLAYBOOK.md")

    assert "PRIVACY_RESTORE_RECONCILIATION_GAP = DOCUMENTED_GAP" in backup
    assert "Reconciliação de privacidade após restore" in recovery
    for evidence in ("conter", "preservar", "tenants", "revogar", "jurídico"):
        assert evidence.casefold() in incident.casefold()


def test_frontend_has_no_token_persistence_tracking_or_transmitting_marketing_form() -> None:
    core = read("app/core.js")
    oidc = read("app/oidc-client.js")
    dashboard = read("app/dashboard-service.js")
    marketing = read("site/marketing.js")
    marketing_html = read("site/index.html")

    assert "localStorage" not in core
    assert "localStorage" not in oidc
    assert "accessToken" not in dashboard
    assert "document.cookie" not in "\n".join((core, oidc, dashboard, marketing))
    assert not any(marker in marketing.casefold() for marker in ("gtag(", "mixpanel", "segment", "fetch("))
    assert "connect-src 'none'" in marketing_html
    assert "form-action 'none'" in marketing_html


def test_metric_schema_cannot_carry_business_or_personal_identifiers() -> None:
    forbidden = {"tenant_id", "company_id", "user_id", "document_id", "cnpj"}
    configured = set().union(*_METRIC_LABELS.values(), *_HISTOGRAM_LABELS.values())
    assert configured.isdisjoint(forbidden)
