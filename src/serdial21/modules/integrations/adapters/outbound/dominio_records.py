'''Representações sem serialização dos campos confirmados da fonte oficial.'''

from dataclasses import dataclass
from decimal import Decimal
from typing import ClassVar


@dataclass(frozen=True, slots=True)
class DominioRecord6000:
    record_code: ClassVar[str] = '6000'
    entry_type: str
    standard_entry_code: str | None
    locator: str | None
    rtt_fcont: str | None


@dataclass(frozen=True, slots=True)
class DominioRecord6100:
    record_code: ClassVar[str] = '6100'
    posting_date: object
    debit_account_reduced_code: object
    credit_account_reduced_code: object
    amount: object
    history_code: object
    history_description: object
    user: str | None
    branch_code: str | None
    scp_code: str | None


@dataclass(frozen=True, slots=True)
class DominioRecord6110:
    record_code: ClassVar[str] = '6110'
    debit_cost_center_code: str | None
    credit_cost_center_code: str | None
    allocation_amount: Decimal


@dataclass(frozen=True, slots=True)
class DominioRecord6130:
    record_code: ClassVar[str] = '6130'
    dfc_item_code: str | None
    amount: Decimal
