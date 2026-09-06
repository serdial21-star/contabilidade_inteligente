'''Identidades dos registros oficiais Domínio; sem campos não incorporados.'''

from dataclasses import dataclass
from typing import ClassVar


@dataclass(frozen=True, slots=True)
class DominioBatch6000:
    '''Registro 6000 — Lançamentos em Lote.'''

    record_code: ClassVar[str] = '6000'


@dataclass(frozen=True, slots=True)
class DominioEntry6100:
    '''Registro 6100 — Lançamentos em Lote – Lançamentos.'''

    record_code: ClassVar[str] = '6100'


@dataclass(frozen=True, slots=True)
class DominioCostCenter6110:
    '''Registro 6110 — Lançamentos em Lote – Lançamentos – Centro de Custos.'''

    record_code: ClassVar[str] = '6110'


@dataclass(frozen=True, slots=True)
class DominioDfc6130:
    '''Registro 6130 — Lançamentos em Lote – Lançamentos – DFC.'''

    record_code: ClassVar[str] = '6130'
