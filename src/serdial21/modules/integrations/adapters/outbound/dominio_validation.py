'''Validação estrutural confirmada; não interpreta campos sem formato oficial.'''

from decimal import Decimal

from serdial21.modules.integrations.adapters.outbound.dominio_records import (
    DominioRecord6000,
    DominioRecord6100,
    DominioRecord6110,
    DominioRecord6130,
)


DominioRecord = DominioRecord6000 | DominioRecord6100 | DominioRecord6110 | DominioRecord6130


def validate_dominio_structure(records: tuple[DominioRecord, ...]) -> None:
    current_batch = False
    current_entry = False
    for record in records:
        if isinstance(record, DominioRecord6000):
            _validate_6000(record)
            current_batch, current_entry = True, False
        elif isinstance(record, DominioRecord6100):
            if not current_batch:
                raise ValueError('registro 6100 exige pai 6000')
            current_entry = True
        elif isinstance(record, (DominioRecord6110, DominioRecord6130)):
            if not current_entry:
                raise ValueError(f'registro {record.record_code} exige pai 6100')
            _validate_decimal(record.allocation_amount if isinstance(record, DominioRecord6110) else record.amount)
        else:
            raise TypeError('registro Domínio não suportado')


def _validate_6000(record: DominioRecord6000) -> None:
    if record.entry_type not in {'D', 'C', 'X', 'V'}:
        raise ValueError('tipo do lançamento 6000 inválido')
    if record.standard_entry_code is not None and not record.standard_entry_code.isdecimal():
        raise ValueError('código do lançamento padrão 6000 deve ser numérico')


def _validate_decimal(value: Decimal) -> None:
    if not isinstance(value, Decimal) or value.as_tuple().exponent != -2:
        raise ValueError('valor decimal Domínio exige exatamente 2 casas decimais')
