'''Marcador imutável para exigir nova conferência após desbloqueio.'''

from dataclasses import dataclass
from enum import StrEnum
from uuid import UUID, uuid4

from serdial21.modules.reconciliation.domain.entities import Reconciliation


class ReconciliationReviewStatus(StrEnum):
    REQUIRES_REVIEW = 'REQUIRES_REVIEW'


@dataclass(frozen=True, slots=True)
class ReconciliationReviewRequirement:
    '''Evento de domínio que a persistência da conciliação projeta como status atual.'''

    id: UUID
    reconciliation_id: UUID
    tenant_id: UUID
    company_id: UUID
    account_lock_id: UUID
    status: ReconciliationReviewStatus


def require_review_after_unlock(
    reconciliation: Reconciliation,
    *,
    account_lock_id: UUID,
) -> ReconciliationReviewRequirement:
    return ReconciliationReviewRequirement(
        uuid4(), reconciliation.id, reconciliation.tenant_id, reconciliation.company_id,
        account_lock_id, ReconciliationReviewStatus.REQUIRES_REVIEW,
    )
