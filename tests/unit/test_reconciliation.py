from datetime import UTC, datetime
from decimal import Decimal
from uuid import uuid4

import pytest

from serdial21.modules.reconciliation.domain.entities import (
    DecisionType,
    MatchOrigin,
    Reconciliation,
    ReconciliationAllocation,
    ReconciliationParticipant,
    ReconciliationStatus,
    ParticipantKind,
    approve,
    assisted_suggestion,
    close,
    create_match,
    deterministic_suggestions,
    open_exception,
    refresh_status,
    reopen,
    request_approval,
)


def setup() -> tuple[Reconciliation, object, object]:
    tenant_id, company_id, ledger_id = uuid4(), uuid4(), uuid4()
    return (
        Reconciliation(uuid4(), tenant_id, company_id, ledger_id, 'BRL', ReconciliationStatus.OPEN),
        tenant_id,
        company_id,
    )


def participant(reconciliation: Reconciliation, kind: ParticipantKind, amount: str) -> ReconciliationParticipant:
    return ReconciliationParticipant(
        uuid4(), reconciliation.id, reconciliation.tenant_id, reconciliation.company_id,
        kind, uuid4(), Decimal(amount),
    )


def allocation(match_id: object, source: ReconciliationParticipant, target: ReconciliationParticipant, amount: str) -> ReconciliationAllocation:
    return ReconciliationAllocation(uuid4(), match_id, source.id, target.id, Decimal(amount))


def test_manual_one_to_one_match_reaches_pending_approval_but_does_not_close() -> None:
    reconciliation, _, _ = setup()
    bank = participant(reconciliation, ParticipantKind.BANK_TRANSACTION, '100.00')
    line = participant(reconciliation, ParticipantKind.JOURNAL_LINE, '100.00')
    match_id = uuid4()
    match = create_match(reconciliation, (bank, line), (allocation(match_id, bank, line, '100.00'),), origin=MatchOrigin.MANUAL)

    assert match.status.value == 'MATCHED'
    pending = request_approval(reconciliation, (match,))
    approved, _ = approve(pending, actor_id=uuid4(), reason='reviewed', decided_at=datetime.now(UTC), authorized=True)
    assert approved.status is ReconciliationStatus.APPROVED


def test_many_to_one_match_is_supported() -> None:
    reconciliation, _, _ = setup()
    first = participant(reconciliation, ParticipantKind.BANK_TRANSACTION, '40')
    second = participant(reconciliation, ParticipantKind.BANK_TRANSACTION, '60')
    line = participant(reconciliation, ParticipantKind.JOURNAL_LINE, '100')
    match_id = uuid4()
    match = create_match(reconciliation, (first, second, line), (
        allocation(match_id, first, line, '40'), allocation(match_id, second, line, '60'),
    ), origin=MatchOrigin.MANUAL)

    assert match.difference == Decimal('0')


def test_partial_and_different_value_remain_unapproved() -> None:
    reconciliation, _, _ = setup()
    bank = participant(reconciliation, ParticipantKind.BANK_TRANSACTION, '100')
    line = participant(reconciliation, ParticipantKind.JOURNAL_LINE, '60')
    match_id = uuid4()
    match = create_match(reconciliation, (bank, line), (allocation(match_id, bank, line, '60'),), origin=MatchOrigin.MANUAL)

    current = refresh_status(reconciliation, (match,))
    assert match.difference == Decimal('40')
    assert current.status is ReconciliationStatus.PARTIALLY_MATCHED
    with pytest.raises(ValueError):
        request_approval(reconciliation, (match,))


def test_duplicate_and_cross_tenant_participants_are_rejected() -> None:
    reconciliation, _, _ = setup()
    bank = participant(reconciliation, ParticipantKind.BANK_TRANSACTION, '10')
    line = participant(reconciliation, ParticipantKind.JOURNAL_LINE, '10')
    match_id = uuid4()
    with pytest.raises(ValueError, match='duplicado'):
        create_match(reconciliation, (bank, line), (allocation(match_id, bank, line, '10'),), origin=MatchOrigin.MANUAL, existing_participants=(bank,))
    foreign = ReconciliationParticipant(uuid4(), reconciliation.id, uuid4(), reconciliation.company_id, ParticipantKind.JOURNAL_LINE, uuid4(), Decimal('10'))
    with pytest.raises(ValueError, match='escopo'):
        create_match(reconciliation, (bank, foreign), (allocation(match_id, bank, foreign, '10'),), origin=MatchOrigin.MANUAL)


def test_exception_prevents_approval() -> None:
    reconciliation, _, _ = setup()
    exceptional, exception = open_exception(reconciliation, code='DUPLICATE', severity='HIGH', reason='same OFX identity')

    assert exceptional.status is ReconciliationStatus.IN_EXCEPTION
    with pytest.raises(ValueError):
        request_approval(exceptional, (), (exception,))


def test_reopen_is_a_decision_and_returns_to_open() -> None:
    reconciliation, _, _ = setup()
    approved = Reconciliation(reconciliation.id, reconciliation.tenant_id, reconciliation.company_id, reconciliation.ledger_id, 'BRL', ReconciliationStatus.APPROVED)
    closed = close(approved)
    reopened, decision = reopen(closed, actor_id=uuid4(), reason='new evidence', decided_at=datetime.now(UTC), authorized=True)

    assert reopened.status is ReconciliationStatus.OPEN
    assert decision.decision is DecisionType.REOPEN


def test_deterministic_and_assisted_suggestions_never_create_match() -> None:
    reconciliation, _, _ = setup()
    bank = participant(reconciliation, ParticipantKind.BANK_TRANSACTION, '10')
    line = participant(reconciliation, ParticipantKind.JOURNAL_LINE, '10')

    deterministic = deterministic_suggestions(reconciliation, (bank, line))
    assisted = assisted_suggestion(reconciliation, (bank, line), participant_ids=(bank.id, line.id), reason_codes=('DESCRIPTION_SIMILARITY',), confidence=Decimal('0.8'))
    assert deterministic[0].origin is MatchOrigin.DETERMINISTIC
    assert assisted.origin is MatchOrigin.ASSISTED
