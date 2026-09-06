'''Conciliação explícita e imutável; não altera a escrituração externa.'''

from dataclasses import dataclass, replace
from datetime import datetime
from decimal import Decimal
from enum import StrEnum
from uuid import UUID, uuid4

from serdial21.modules.accounting.domain.entities import JournalLine
from serdial21.modules.banking.domain.entities import BankTransaction


ZERO = Decimal('0')


class ReconciliationStatus(StrEnum):
    OPEN = 'OPEN'
    PARTIALLY_MATCHED = 'PARTIALLY_MATCHED'
    MATCHED = 'MATCHED'
    PENDING_APPROVAL = 'PENDING_APPROVAL'
    APPROVED = 'APPROVED'
    CLOSED = 'CLOSED'
    IN_EXCEPTION = 'IN_EXCEPTION'


class ParticipantKind(StrEnum):
    BANK_TRANSACTION = 'BANK_TRANSACTION'
    JOURNAL_LINE = 'JOURNAL_LINE'


class MatchOrigin(StrEnum):
    MANUAL = 'MANUAL'
    DETERMINISTIC = 'DETERMINISTIC'
    ASSISTED = 'ASSISTED'


class MatchStatus(StrEnum):
    PARTIAL = 'PARTIAL'
    MATCHED = 'MATCHED'


class DecisionType(StrEnum):
    APPROVE = 'APPROVE'
    REOPEN = 'REOPEN'


@dataclass(frozen=True, slots=True)
class Reconciliation:
    id: UUID
    tenant_id: UUID
    company_id: UUID
    ledger_id: UUID
    currency_code: str
    status: ReconciliationStatus


@dataclass(frozen=True, slots=True)
class ReconciliationParticipant:
    id: UUID
    reconciliation_id: UUID
    tenant_id: UUID
    company_id: UUID
    kind: ParticipantKind
    subject_id: UUID
    amount: Decimal


@dataclass(frozen=True, slots=True)
class ReconciliationAllocation:
    id: UUID
    match_id: UUID
    source_participant_id: UUID
    target_participant_id: UUID
    amount: Decimal


@dataclass(frozen=True, slots=True)
class ReconciliationMatch:
    id: UUID
    reconciliation_id: UUID
    tenant_id: UUID
    company_id: UUID
    origin: MatchOrigin
    confidence: Decimal | None
    difference: Decimal
    status: MatchStatus


@dataclass(frozen=True, slots=True)
class ReconciliationException:
    id: UUID
    reconciliation_id: UUID
    tenant_id: UUID
    company_id: UUID
    code: str
    severity: str
    reason: str
    match_id: UUID | None


@dataclass(frozen=True, slots=True)
class ReconciliationDecision:
    id: UUID
    reconciliation_id: UUID
    tenant_id: UUID
    company_id: UUID
    decision: DecisionType
    actor_id: UUID
    reason: str
    decided_at: datetime


@dataclass(frozen=True, slots=True)
class ReconciliationSuggestion:
    '''Uma hipótese explicável. A aplicação deve convertê-la em match manual.'''

    origin: MatchOrigin
    participant_ids: tuple[UUID, ...]
    reason_codes: tuple[str, ...]
    confidence: Decimal | None


def participant_from_bank_transaction(
    reconciliation_id: UUID,
    transaction: BankTransaction,
) -> ReconciliationParticipant:
    return ReconciliationParticipant(
        uuid4(), reconciliation_id, transaction.tenant_id, transaction.company_id,
        ParticipantKind.BANK_TRANSACTION, transaction.id, _positive(transaction.amount),
    )


def participant_from_journal_line(
    reconciliation_id: UUID,
    line: JournalLine,
) -> ReconciliationParticipant:
    if line.debit < ZERO or line.credit < ZERO or bool(line.debit) == bool(line.credit):
        raise ValueError('JournalLine deve possuir exatamente um valor positivo')
    return ReconciliationParticipant(
        uuid4(), reconciliation_id, line.tenant_id, line.company_id,
        ParticipantKind.JOURNAL_LINE, line.id, line.debit or line.credit,
    )


def create_match(
    reconciliation: Reconciliation,
    participants: tuple[ReconciliationParticipant, ...],
    allocations: tuple[ReconciliationAllocation, ...],
    *,
    origin: MatchOrigin,
    confidence: Decimal | None = None,
    existing_participants: tuple[ReconciliationParticipant, ...] = (),
) -> ReconciliationMatch:
    _require_mutable(reconciliation)
    _validate_confidence(origin, confidence)
    _validate_participants(reconciliation, participants, existing_participants)
    match_id = allocations[0].match_id if allocations else uuid4()
    _validate_allocations(match_id, participants, allocations)
    bank_total = sum(
        (participant.amount for participant in participants
         if participant.kind is ParticipantKind.BANK_TRANSACTION), ZERO,
    )
    journal_total = sum(
        (participant.amount for participant in participants
         if participant.kind is ParticipantKind.JOURNAL_LINE), ZERO,
    )
    difference = abs(bank_total - journal_total)
    return ReconciliationMatch(
        match_id, reconciliation.id, reconciliation.tenant_id, reconciliation.company_id,
        origin, confidence, difference,
        MatchStatus.MATCHED if difference == ZERO else MatchStatus.PARTIAL,
    )


def refresh_status(
    reconciliation: Reconciliation,
    matches: tuple[ReconciliationMatch, ...],
    exceptions: tuple[ReconciliationException, ...] = (),
) -> Reconciliation:
    _require_mutable(reconciliation)
    _validate_children_scope(reconciliation, matches, exceptions)
    if exceptions:
        return replace(reconciliation, status=ReconciliationStatus.IN_EXCEPTION)
    if not matches:
        return replace(reconciliation, status=ReconciliationStatus.OPEN)
    if any(match.status is MatchStatus.PARTIAL for match in matches):
        return replace(reconciliation, status=ReconciliationStatus.PARTIALLY_MATCHED)
    return replace(reconciliation, status=ReconciliationStatus.MATCHED)


def deterministic_suggestions(
    reconciliation: Reconciliation,
    participants: tuple[ReconciliationParticipant, ...],
) -> tuple[ReconciliationSuggestion, ...]:
    _validate_participants(reconciliation, participants, ())
    banks = sorted(
        (item for item in participants if item.kind is ParticipantKind.BANK_TRANSACTION),
        key=lambda item: str(item.id),
    )
    journals = sorted(
        (item for item in participants if item.kind is ParticipantKind.JOURNAL_LINE),
        key=lambda item: str(item.id),
    )
    return tuple(
        ReconciliationSuggestion(
            MatchOrigin.DETERMINISTIC, (bank.id, journal.id),
            ('EXACT_AMOUNT',), Decimal('1'),
        )
        for bank in banks for journal in journals if bank.amount == journal.amount
    )


def assisted_suggestion(
    reconciliation: Reconciliation,
    participants: tuple[ReconciliationParticipant, ...],
    *,
    participant_ids: tuple[UUID, ...],
    reason_codes: tuple[str, ...],
    confidence: Decimal,
) -> ReconciliationSuggestion:
    _validate_participants(reconciliation, participants, ())
    if len(participant_ids) < 2 or len(set(participant_ids)) != len(participant_ids):
        raise ValueError('sugestão assistida exige participantes distintos')
    if set(participant_ids) - {participant.id for participant in participants}:
        raise ValueError('sugestão assistida referencia participante desconhecido')
    if not reason_codes or any(not code.strip() for code in reason_codes):
        raise ValueError('sugestão assistida exige reason codes')
    _validate_confidence(MatchOrigin.ASSISTED, confidence)
    return ReconciliationSuggestion(
        MatchOrigin.ASSISTED, participant_ids, reason_codes, confidence,
    )


def open_exception(
    reconciliation: Reconciliation,
    *,
    code: str,
    severity: str,
    reason: str,
    match_id: UUID | None = None,
) -> tuple[Reconciliation, ReconciliationException]:
    _require_mutable(reconciliation)
    if not code.strip() or not severity.strip() or not reason.strip():
        raise ValueError('exceção exige código, severidade e motivo')
    exception = ReconciliationException(
        uuid4(), reconciliation.id, reconciliation.tenant_id, reconciliation.company_id,
        code, severity, reason, match_id,
    )
    return replace(reconciliation, status=ReconciliationStatus.IN_EXCEPTION), exception


def request_approval(
    reconciliation: Reconciliation,
    matches: tuple[ReconciliationMatch, ...],
    exceptions: tuple[ReconciliationException, ...] = (),
) -> Reconciliation:
    current = refresh_status(reconciliation, matches, exceptions)
    if current.status is not ReconciliationStatus.MATCHED:
        raise ValueError('aprovação exige conciliação sem diferença e sem exceção')
    return replace(current, status=ReconciliationStatus.PENDING_APPROVAL)


def approve(
    reconciliation: Reconciliation,
    *,
    actor_id: UUID,
    reason: str,
    decided_at: datetime,
    authorized: bool,
) -> tuple[Reconciliation, ReconciliationDecision]:
    if reconciliation.status is not ReconciliationStatus.PENDING_APPROVAL:
        raise ValueError('aprovação exige conciliação pendente')
    if not authorized:
        raise PermissionError('ator não autorizado a aprovar conciliação')
    return _decision(reconciliation, ReconciliationStatus.APPROVED, DecisionType.APPROVE,
                     actor_id, reason, decided_at)


def close(reconciliation: Reconciliation) -> Reconciliation:
    if reconciliation.status is not ReconciliationStatus.APPROVED:
        raise ValueError('fechamento exige conciliação aprovada')
    return replace(reconciliation, status=ReconciliationStatus.CLOSED)


def reopen(
    reconciliation: Reconciliation,
    *,
    actor_id: UUID,
    reason: str,
    decided_at: datetime,
    authorized: bool,
) -> tuple[Reconciliation, ReconciliationDecision]:
    if reconciliation.status not in (ReconciliationStatus.APPROVED, ReconciliationStatus.CLOSED):
        raise ValueError('reabertura exige conciliação aprovada ou fechada')
    if not authorized:
        raise PermissionError('ator não autorizado a reabrir conciliação')
    return _decision(reconciliation, ReconciliationStatus.OPEN, DecisionType.REOPEN,
                     actor_id, reason, decided_at)


def _decision(
    reconciliation: Reconciliation,
    next_status: ReconciliationStatus,
    decision: DecisionType,
    actor_id: UUID,
    reason: str,
    decided_at: datetime,
) -> tuple[Reconciliation, ReconciliationDecision]:
    if not reason.strip():
        raise ValueError('decisão exige justificativa')
    if decided_at.tzinfo is None or decided_at.utcoffset() is None:
        raise ValueError('decisão exige timestamp com timezone')
    return replace(reconciliation, status=next_status), ReconciliationDecision(
        uuid4(), reconciliation.id, reconciliation.tenant_id, reconciliation.company_id,
        decision, actor_id, reason, decided_at,
    )


def _validate_participants(
    reconciliation: Reconciliation,
    participants: tuple[ReconciliationParticipant, ...],
    existing: tuple[ReconciliationParticipant, ...],
) -> None:
    if len(participants) < 2:
        raise ValueError('match exige pelo menos dois participantes')
    seen = {(item.kind, item.subject_id) for item in existing}
    kinds: set[ParticipantKind] = set()
    for participant in participants:
        if (participant.reconciliation_id, participant.tenant_id, participant.company_id) != (
            reconciliation.id, reconciliation.tenant_id, reconciliation.company_id,
        ):
            raise ValueError('participante fora do escopo da conciliação')
        if not isinstance(participant.amount, Decimal) or participant.amount <= ZERO:
            raise ValueError('participante exige Decimal positivo')
        identity = (participant.kind, participant.subject_id)
        if identity in seen:
            raise ValueError('participante duplicado na conciliação')
        seen.add(identity)
        kinds.add(participant.kind)
    if kinds != {ParticipantKind.BANK_TRANSACTION, ParticipantKind.JOURNAL_LINE}:
        raise ValueError('match exige movimento bancário e linha contábil')


def _validate_allocations(
    match_id: UUID,
    participants: tuple[ReconciliationParticipant, ...],
    allocations: tuple[ReconciliationAllocation, ...],
) -> None:
    if not allocations:
        raise ValueError('match exige alocação explícita')
    by_id = {participant.id: participant for participant in participants}
    allocated: dict[UUID, Decimal] = {participant.id: ZERO for participant in participants}
    for allocation in allocations:
        if allocation.match_id != match_id or not isinstance(allocation.amount, Decimal):
            raise ValueError('alocação inválida')
        if allocation.amount <= ZERO:
            raise ValueError('alocação exige Decimal positivo')
        source = by_id.get(allocation.source_participant_id)
        target = by_id.get(allocation.target_participant_id)
        if source is None or target is None or source.kind is target.kind:
            raise ValueError('alocação exige participantes de lados distintos')
        allocated[source.id] += allocation.amount
        allocated[target.id] += allocation.amount
    if any(allocated[item.id] > item.amount for item in participants):
        raise ValueError('alocação excede valor disponível')


def _validate_children_scope(
    reconciliation: Reconciliation,
    matches: tuple[ReconciliationMatch, ...],
    exceptions: tuple[ReconciliationException, ...],
) -> None:
    for child in (*matches, *exceptions):
        if (child.reconciliation_id, child.tenant_id, child.company_id) != (
            reconciliation.id, reconciliation.tenant_id, reconciliation.company_id,
        ):
            raise ValueError('filho fora do escopo da conciliação')


def _validate_confidence(origin: MatchOrigin, confidence: Decimal | None) -> None:
    if origin is MatchOrigin.MANUAL:
        if confidence is not None:
            raise ValueError('match manual não possui confiança automática')
        return
    if not isinstance(confidence, Decimal) or not ZERO <= confidence <= Decimal('1'):
        raise ValueError('sugestão exige confiança Decimal entre zero e um')


def _require_mutable(reconciliation: Reconciliation) -> None:
    if reconciliation.status in (ReconciliationStatus.APPROVED, ReconciliationStatus.CLOSED):
        raise ValueError('conciliação aprovada ou fechada exige reabertura')


def _positive(value: Decimal) -> Decimal:
    if not isinstance(value, Decimal) or value == ZERO:
        raise ValueError('movimento bancário exige Decimal diferente de zero')
    return abs(value)
