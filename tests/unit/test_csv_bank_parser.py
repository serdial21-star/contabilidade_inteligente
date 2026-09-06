from decimal import Decimal
from uuid import uuid4

import pytest

from serdial21.modules.banking.adapters.inbound.csv import CsvBankStatementParser
from serdial21.modules.banking.domain.csv_layout import CsvBankLayout


def _layout(**changes: object) -> CsvBankLayout:
    columns = changes.pop('columns', {
        'date': 'Data', 'description': 'Historico', 'document_number': 'Documento',
        'amount': 'Valor', 'balance': 'Saldo', 'external_reference': 'Identificador',
    })
    layout = CsvBankLayout.draft(uuid4(), uuid4(), 'Genérico', columns=columns, **changes)
    return layout.publish()


def test_preview_comma_decimal_and_brazilian_date() -> None:
    layout = _layout(delimiter=';', decimal_separator=',', thousands_separator='.', date_format='%d/%m/%Y')
    preview = CsvBankStatementParser().preview(
        'Data;HistÃƒÂ³rico;Documento;Valor;Saldo;Identificador\n05/09/2026;Pix;42;-1.234,56;100,00;abc\n'.encode(), layout)
    transaction = preview.valid_transactions[0]
    assert transaction.transaction_date.isoformat() == '2026-09-05'
    assert transaction.amount == Decimal('-1234.56')
    assert transaction.direction == 'DEBIT'
    assert not preview.issues


def test_preview_comma_separator_iso_date_and_explicit_debit_credit() -> None:
    layout = _layout(columns={'date': '0', 'description': '1', 'debit': '2', 'credit': '3'},
                     delimiter=',', has_header=False, sign_policy='DEBIT_CREDIT_COLUMNS')
    preview = CsvBankStatementParser().preview(b'2026-09-05,Recebimento,,42.10\n', layout)
    assert preview.valid_transactions[0].amount == Decimal('42.10')
    assert preview.valid_transactions[0].direction == 'CREDIT'


def test_preview_reports_invalid_date_without_importing_row() -> None:
    content = 'Data,Historico,Documento,Valor,Saldo,Identificador\n31/02/2026,x,,1,,\n'.encode()
    preview = CsvBankStatementParser().preview(content, _layout(date_format='%d/%m/%Y'))
    assert preview.issues[0].code == 'INVALID_CSV_ROW'


def test_published_layout_is_immutable_and_new_version_is_draft() -> None:
    layout = _layout()
    with pytest.raises(ValueError, match='rascunho'):
        layout.publish()
    assert layout.next_version(delimiter=';').version == 2
