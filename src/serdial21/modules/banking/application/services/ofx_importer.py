'''Orquestra a importa\u00e7\u00e3o OFX sem atribuir significado cont\u00e1bil ao sinal.''' 

from collections.abc import Callable
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from hashlib import sha256
import json
from uuid import UUID, uuid4

from serdial21.modules.audit.application.services.audit import AuditRecord, AuditService
from serdial21.modules.banking.application.ports.parser import OfxParseError, OfxParser
from serdial21.modules.banking.application.ports.repository import BankingRepository
from serdial21.modules.banking.domain.entities import BankAccount, BankStatement, BankTransaction, ParsedOfx
from serdial21.modules.intake_documents.application.services.intake import (
    DocumentIntakeService, IntakeContext, LineageRequest, TransformationRequest,
    UploadRequest, ValidationIssueRequest,
)


CANONICAL_SCHEMA_VERSION = 'serdial21.banking.ofx/v1'
SIGN_POLICY = 'OFX_TRNAMT_SIGN_PRESERVED_V1'


@dataclass(frozen=True, slots=True)
class OfxImportRequest:
    batch_id: UUID
    content: bytes
    original_filename: str
    external_key: str | None = None


@dataclass(frozen=True, slots=True)
class OfxImportResult:
    status: str
    artifact_id: UUID
    receipt_id: UUID
    transformation_run_id: UUID | None
    account_ids: tuple[UUID, ...]
    statement_ids: tuple[UUID, ...]
    imported_transactions: int
    duplicate_transactions: int
    issue_codes: tuple[str, ...]


class OfxImportService:
    def __init__(self, intake: DocumentIntakeService, parser: OfxParser, repository: BankingRepository,
                 audit: AuditService, *, id_factory: Callable[[], UUID] = uuid4,
                 clock: Callable[[], datetime] | None = None) -> None:
        self._intake, self._parser, self._repository, self._audit = intake, parser, repository, audit
        self._id_factory, self._clock = id_factory, clock or (lambda: datetime.now(UTC))

    def import_ofx(self, context: IntakeContext, request: OfxImportRequest) -> OfxImportResult:
        upload = self._intake.upload(context, UploadRequest(
            batch_id=request.batch_id, content=request.content, original_filename=request.original_filename,
            media_type='application/x-ofx', classification='BANK_STATEMENT_OFX', channel='OFX_IMPORT',
            external_key=request.external_key,
        ))
        try:
            parsed = self._parser.parse(request.content)
        except OfxParseError as error:
            run = self._intake.record_transformation(context, TransformationRequest(
                artifact_id=upload.artifact_id, previous_run_id=None, parser_name=self._parser.parser_name,
                parser_version=self._parser.parser_version, schema_version=error.schema_version,
                output_hash=None, status='FAILED'))
            self._intake.add_validation_issue(context, ValidationIssueRequest(
                transformation_run_id=run.id, code=error.code, severity='ERROR', field_path=None,
                rule_reference=error.schema_version, message=str(error), resolution_status='QUARANTINED'))
            return OfxImportResult('QUARANTINED', upload.artifact_id, upload.receipt_id, run.id, (), (), 0, 0, (error.code,))

        self._intake.require_access(context)
        run = self._intake.record_transformation(context, TransformationRequest(
            artifact_id=upload.artifact_id, previous_run_id=None, parser_name=self._parser.parser_name,
            parser_version=self._parser.parser_version, schema_version=parsed.schema_version,
            output_hash=_fingerprint(parsed), status='COMPLETED'))
        self._intake.add_lineage(context, LineageRequest('ArtifactReceipt', upload.receipt_id, None,
            'TransformationRun', run.id, None, run.id, 'PROCESSED_BY'))
        account_ids: list[UUID] = []
        statement_ids: list[UUID] = []
        imported = duplicates = 0
        now = self._now()
        for item in parsed.statements:
            external_identity = _account_identity(item.bank_id, item.branch_id, item.account_number, item.account_type)
            account = self._repository.find_account(context.tenant_id, context.company_id, external_identity)
            if account is None:
                account = BankAccount(self._id_factory(), context.tenant_id, context.company_id, item.bank_id,
                    item.branch_id, item.account_number, item.account_type, item.currency_code,
                    external_identity, now)
                self._repository.add_account(account)
            account_ids.append(account.id)
            statement = self._repository.find_statement_by_artifact(context.tenant_id, context.company_id, account.id, upload.artifact_id)
            if statement is None:
                statement = BankStatement(self._id_factory(), context.tenant_id, context.company_id, account.id,
                    upload.artifact_id, run.id, parsed.schema_version, item.start_date, item.end_date,
                    item.opening_balance, item.closing_balance, item.currency_code, SIGN_POLICY,
                    upload.content_hash, _fingerprint(item), now)
                self._repository.add_statement(statement)
                for transaction in item.transactions:
                    identity_kind = 'FITID' if transaction.fitid else 'FINGERPRINT'
                    fingerprint = _transaction_fingerprint(account.external_identity, transaction)
                    duplicate = (self._repository.find_transaction_by_fitid(context.tenant_id, context.company_id, account.id, transaction.fitid)
                                 if transaction.fitid else self._repository.find_transaction_by_fingerprint(context.tenant_id, context.company_id, account.id, fingerprint))
                    if duplicate is not None:
                        duplicates += 1
                        continue
                    self._repository.add_transaction(BankTransaction(self._id_factory(), context.tenant_id,
                        context.company_id, statement.id, account.id, transaction.fitid, transaction.external_reference,
                        transaction.transaction_date, transaction.posted_date, transaction.amount,
                        transaction.direction, transaction.description, transaction.document_number, fingerprint,
                        identity_kind, now))
                    imported += 1
            statement_ids.append(statement.id)
        self._audit.record(AuditRecord(tenant_id=context.tenant_id, company_id=context.company_id,
            actor_id=context.actor_id, origin=context.origin, module='banking', action='ofx.imported',
            subject_type='TransformationRun', subject_id=run.id, subject_version=None, before=None,
            after={'schema_version': parsed.schema_version, 'account_count': len(account_ids),
                   'statement_count': len(statement_ids), 'imported_transactions': imported,
                   'duplicate_transactions': duplicates, 'sign_policy': SIGN_POLICY}, reason=None,
            correlation_id=context.correlation_id, causation_id=context.causation_id))
        return OfxImportResult('IMPORTED', upload.artifact_id, upload.receipt_id, run.id, tuple(account_ids),
            tuple(statement_ids), imported, duplicates, ())

    def _now(self) -> datetime:
        value = self._clock()
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError('rel\u00f3gio deve retornar datetime com timezone')
        return value.astimezone(UTC)


def _account_identity(bank: str | None, branch: str | None, account: str, account_type: str | None) -> str:
    return '|'.join((bank or '', branch or '', account, account_type or ''))


def _fingerprint(value: object) -> str:
    return sha256(json.dumps(_json_value(asdict(value)), ensure_ascii=False, sort_keys=True,
                             separators=(',', ':')).encode('utf-8')).hexdigest()


def _transaction_fingerprint(account_identity: str, transaction: object) -> str:
    return _fingerprint({'account_identity': account_identity, **asdict(transaction)})


def _json_value(value: object) -> object:
    from datetime import date
    from decimal import Decimal
    if isinstance(value, dict): return {str(k): _json_value(v) for k, v in value.items()}
    if isinstance(value, (tuple, list)): return [_json_value(v) for v in value]
    if isinstance(value, (datetime, date)): return value.isoformat()
    if isinstance(value, Decimal): return str(value)
    return value
