'''Layout CSV bancário versionado; regras puras, sem detalhes de transporte.''' 

from dataclasses import dataclass, replace
from uuid import UUID, uuid4


MAPPABLE_FIELDS = frozenset({
    'date', 'description', 'document_number', 'debit', 'credit', 'amount',
    'balance', 'external_reference',
})
SIGN_POLICIES = frozenset({'AMOUNT_PRESERVED', 'DEBIT_CREDIT_COLUMNS'})


@dataclass(frozen=True, slots=True)
class CsvBankLayout:
    id: UUID
    tenant_id: UUID
    company_id: UUID
    name: str
    version: int
    status: str
    columns: dict[str, str]
    delimiter: str
    decimal_separator: str
    thousands_separator: str | None
    encoding: str
    date_format: str
    has_header: bool
    sign_policy: str

    @classmethod
    def draft(cls, tenant_id: UUID, company_id: UUID, name: str, *, columns: dict[str, str],
              delimiter: str = ',', decimal_separator: str = '.',
              thousands_separator: str | None = None, encoding: str = 'utf-8',
              date_format: str = '%Y-%m-%d', has_header: bool = True,
              sign_policy: str = 'AMOUNT_PRESERVED') -> 'CsvBankLayout':
        layout = cls(uuid4(), tenant_id, company_id, name, 1, 'DRAFT', columns, delimiter,
                     decimal_separator, thousands_separator, encoding, date_format,
                     has_header, sign_policy)
        layout.validate()
        return layout

    def publish(self) -> 'CsvBankLayout':
        self.validate()
        if self.status != 'DRAFT':
            raise ValueError('somente layout em rascunho pode ser publicado')
        return replace(self, status='PUBLISHED')

    def next_version(self, **changes: object) -> 'CsvBankLayout':
        if self.status != 'PUBLISHED':
            raise ValueError('nova versão exige layout publicado')
        candidate = replace(self, id=uuid4(), version=self.version + 1, status='DRAFT', **changes)
        candidate.validate()
        return candidate

    def validate(self) -> None:
        if not self.name.strip() or self.version < 1:
            raise ValueError('nome e versão válida são obrigatórios')
        if len(self.delimiter) != 1 or self.delimiter in {'\r', '\n'}:
            raise ValueError('separador inválido')
        if self.decimal_separator not in {'.', ','}:
            raise ValueError('separador decimal inválido')
        if self.thousands_separator == self.decimal_separator:
            raise ValueError('separadores decimal e de milhares não podem coincidir')
        if self.sign_policy not in SIGN_POLICIES:
            raise ValueError('política de sinal inválida')
        unknown = set(self.columns) - MAPPABLE_FIELDS
        if unknown or not self.columns.get('date'):
            raise ValueError('mapeamento CSV inválido')
        if self.sign_policy == 'AMOUNT_PRESERVED' and not self.columns.get('amount'):
            raise ValueError('política AMOUNT_PRESERVED exige a coluna amount')
        if self.sign_policy == 'DEBIT_CREDIT_COLUMNS' and not (self.columns.get('debit') or self.columns.get('credit')):
            raise ValueError('política DEBIT_CREDIT_COLUMNS exige débito ou crédito')
