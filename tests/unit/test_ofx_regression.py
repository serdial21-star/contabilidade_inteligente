'''Regressão do OFX: sinal de origem e deduplicação entre extratos.'''

from dataclasses import dataclass
from hashlib import sha256
from types import SimpleNamespace
from uuid import UUID, uuid4

from serdial21.modules.banking.adapters.inbound.ofx import SafeOfxParser
from serdial21.modules.banking.application.services.ofx_importer import (
    OfxImportRequest,
    OfxImportService,
)
from serdial21.modules.banking.domain.entities import (
    BankAccount,
    BankStatement,
    BankTransaction,
)
from serdial21.modules.intake_documents.application.services.intake import (
    IntakeContext,
    UploadResult,
)
from serdial21.modules.audit.domain.entities import AuditOrigin


OFX = b'''<?xml version="1.0" encoding="UTF-8"?>
<OFX VERSION="2.0">
  <BANKMSGSRSV1><STMTTRNRS><STMTRS>
    <CURDEF>BRL</CURDEF>
    <BANKACCTFROM><BANKID>001</BANKID><BRANCHID>1234</BRANCHID><ACCTID>000123</ACCTID><ACCTTYPE>CHECKING</ACCTTYPE></BANKACCTFROM>
    <BANKTRANLIST><DTSTART>20260901</DTSTART><DTEND>20260902</DTEND>
      <STMTTRN><TRNTYPE>DEBIT</TRNTYPE><DTPOSTED>20260902</DTPOSTED><TRNAMT>-25.40</TRNAMT><FITID>bank-transaction-1</FITID><MEMO>Pagamento</MEMO></STMTTRN>
    </BANKTRANLIST>
    <LEDGERBAL><BALAMT>100.00</BALAMT></LEDGERBAL>
  </STMTRS></STMTTRNRS></BANKMSGSRSV1>
</OFX>'''


class Intake:
    def __init__(self) -> None:
        self.uploads = 0

    def upload(self, context: IntakeContext, request: object) -> UploadResult:
        self.uploads += 1
        content = request.content  # type: ignore[attr-defined]
        return UploadResult(
            artifact_id=uuid4(), receipt_id=uuid4(), import_item_id=uuid4(),
            content_hash=sha256(content).hexdigest(), storage_key='test/object',
            duplicate=False,
        )

    def require_access(self, context: IntakeContext) -> None:
        return None

    def record_transformation(self, context: IntakeContext, request: object) -> object:
        return SimpleNamespace(id=uuid4())

    def add_lineage(self, context: IntakeContext, request: object) -> None:
        return None

    def add_validation_issue(self, context: IntakeContext, request: object) -> None:
        return None


class Repository:
    def __init__(self) -> None:
        self.accounts: list[BankAccount] = []
        self.statements: list[BankStatement] = []
        self.transactions: list[BankTransaction] = []

    def find_account(self, tenant_id: UUID, company_id: UUID, external_identity: str) -> BankAccount | None:
        return next((item for item in self.accounts if item.tenant_id == tenant_id and item.company_id == company_id and item.external_identity == external_identity), None)

    def add_account(self, account: BankAccount) -> None:
        self.accounts.append(account)

    def find_statement_by_artifact(self, tenant_id: UUID, company_id: UUID, bank_account_id: UUID, artifact_id: UUID) -> BankStatement | None:
        return next((item for item in self.statements if item.tenant_id == tenant_id and item.company_id == company_id and item.bank_account_id == bank_account_id and item.artifact_id == artifact_id), None)

    def add_statement(self, statement: BankStatement) -> None:
        self.statements.append(statement)

    def find_transaction_by_fitid(self, tenant_id: UUID, company_id: UUID, bank_account_id: UUID, fitid: str) -> BankTransaction | None:
        return next((item for item in self.transactions if item.tenant_id == tenant_id and item.company_id == company_id and item.bank_account_id == bank_account_id and item.fitid == fitid), None)

    def find_transaction_by_fingerprint(self, tenant_id: UUID, company_id: UUID, bank_account_id: UUID, fingerprint: str) -> BankTransaction | None:
        return next((item for item in self.transactions if item.tenant_id == tenant_id and item.company_id == company_id and item.bank_account_id == bank_account_id and item.fingerprint == fingerprint), None)

    def add_transaction(self, transaction: BankTransaction) -> None:
        self.transactions.append(transaction)


@dataclass
class Audit:
    records: list[object]

    def record(self, record: object) -> None:
        self.records.append(record)


def test_ofx_preserves_sign_and_deduplicates_fitid_across_statements() -> None:
    parsed = SafeOfxParser().parse(OFX)
    transaction = parsed.statements[0].transactions[0]
    assert transaction.amount.as_tuple().sign == 1
    assert transaction.direction == 'DEBIT'

    tenant_id, company_id = uuid4(), uuid4()
    context = IntakeContext(tenant_id, company_id, uuid4(), AuditOrigin.HUMAN, uuid4())
    repository = Repository()
    service = OfxImportService(Intake(), SafeOfxParser(), repository, Audit([]))
    first = service.import_ofx(context, OfxImportRequest(uuid4(), OFX, 'first.ofx'))
    second = service.import_ofx(context, OfxImportRequest(uuid4(), OFX + b'\n', 'second.ofx'))

    assert first.imported_transactions == 1
    assert second.imported_transactions == 0
    assert second.duplicate_transactions == 1
    assert len(repository.transactions) == 1
