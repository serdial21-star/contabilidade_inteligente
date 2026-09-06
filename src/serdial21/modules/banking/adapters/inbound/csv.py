'''Parser CSV genérico dirigido por layout publicado, sem código por banco.''' 

import csv
from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from io import StringIO

from serdial21.modules.banking.domain.csv_layout import CsvBankLayout


@dataclass(frozen=True, slots=True)
class CsvTransaction:
    transaction_date: date
    description: str | None
    document_number: str | None
    external_reference: str | None
    amount: Decimal
    direction: str
    balance: Decimal | None


@dataclass(frozen=True, slots=True)
class CsvValidationIssue:
    row_number: int
    code: str
    field: str | None
    message: str


@dataclass(frozen=True, slots=True)
class CsvPreview:
    layout_id: str
    layout_version: int
    valid_transactions: tuple[CsvTransaction, ...]
    issues: tuple[CsvValidationIssue, ...]


class CsvBankStatementParser:
    parser_name = 'serdial21.banking.csv'
    parser_version = '1.0.0'

    def preview(self, content: bytes, layout: CsvBankLayout, *, max_rows: int = 100) -> CsvPreview:
        if layout.status != 'PUBLISHED':
            raise ValueError('preview exige layout publicado')
        try:
            text = content.decode(layout.encoding)
        except UnicodeDecodeError as error:
            raise ValueError('CSV não corresponde ao encoding do layout') from error
        reader = csv.DictReader(StringIO(text), delimiter=layout.delimiter) if layout.has_header else csv.reader(StringIO(text), delimiter=layout.delimiter)
        valid: list[CsvTransaction] = []
        issues: list[CsvValidationIssue] = []
        for position, row in enumerate(reader, start=2 if layout.has_header else 1):
            if position > max_rows + (1 if layout.has_header else 0):
                break
            try:
                valid.append(_transaction(row, layout))
            except ValueError as error:
                issues.append(CsvValidationIssue(position, 'INVALID_CSV_ROW', None, str(error)))
        return CsvPreview(str(layout.id), layout.version, tuple(valid), tuple(issues))


def _transaction(row: dict[str, str | None] | list[str], layout: CsvBankLayout) -> CsvTransaction:
    get = lambda field: _column(row, layout.columns.get(field), layout.has_header)
    raw_date = get('date')
    if not raw_date:
        raise ValueError('data obrigatória ausente')
    try:
        transaction_date = datetime.strptime(raw_date, layout.date_format).date()
    except ValueError as error:
        raise ValueError('data inválida para o formato configurado') from error
    if layout.sign_policy == 'AMOUNT_PRESERVED':
        amount = _decimal(get('amount'), layout)
        if amount is None:
            raise ValueError('valor obrigatório ausente')
    else:
        debit, credit = _decimal(get('debit'), layout), _decimal(get('credit'), layout)
        if debit is None and credit is None:
            raise ValueError('débito ou crédito obrigatório ausente')
        amount = (credit or Decimal('0')) - (debit or Decimal('0'))
    balance = _decimal(get('balance'), layout)
    return CsvTransaction(transaction_date, get('description'), get('document_number'),
                          get('external_reference'), amount,
                          'DEBIT' if amount < 0 else 'CREDIT' if amount > 0 else 'ZERO', balance)


def _column(row: dict[str, str | None] | list[str], reference: str | None, has_header: bool) -> str | None:
    if not reference:
        return None
    if has_header:
        assert isinstance(row, dict)
        return row.get(reference)
    try:
        assert isinstance(row, list)
        return row[int(reference)]
    except (AssertionError, IndexError, ValueError) as error:
        raise ValueError(f'coluna {reference!r} ausente') from error


def _decimal(value: str | None, layout: CsvBankLayout) -> Decimal | None:
    if value is None or not value.strip():
        return None
    normalized = value.strip()
    if layout.thousands_separator:
        normalized = normalized.replace(layout.thousands_separator, '')
    normalized = normalized.replace(layout.decimal_separator, '.')
    try:
        result = Decimal(normalized)
    except InvalidOperation as error:
        raise ValueError('valor decimal inválido') from error
    if not result.is_finite() or result.as_tuple().exponent < -2:
        raise ValueError('valor fora da precisão monetária')
    return result
