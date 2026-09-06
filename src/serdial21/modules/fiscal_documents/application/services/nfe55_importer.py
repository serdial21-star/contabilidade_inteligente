'''Orquestra a importação idempotente da NF-e modelo 55.'''

from collections.abc import Callable
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from decimal import Decimal
from hashlib import sha256
import json
from uuid import UUID, uuid4

from serdial21.modules.audit.application.services.audit import AuditRecord, AuditService
from serdial21.modules.fiscal_documents.application.ports.parser import (
    FiscalXmlParseError,
    NFe55Parser,
)
from serdial21.modules.fiscal_documents.application.ports.repository import (
    FiscalDocumentRepository,
)
from serdial21.modules.fiscal_documents.domain.entities import (
    CanonicalRecord,
    FiscalDocument,
    FiscalDocumentItem,
    ParsedNFe55,
    ParsedValidationIssue,
    TaxDetail,
)
from serdial21.modules.intake_documents.application.services.intake import (
    DocumentIntakeService,
    IntakeContext,
    LineageRequest,
    TransformationRequest,
    UploadRequest,
    ValidationIssueRequest,
)
from serdial21.modules.intake_documents.domain.entities import TransformationRun


CANONICAL_SCHEMA_VERSION = 'serdial21.fiscal.nfe55/v1'


@dataclass(frozen=True, slots=True)
class NFe55ImportRequest:
    batch_id: UUID
    content: bytes
    original_filename: str
    external_key: str | None = None


@dataclass(frozen=True, slots=True)
class NFe55ImportResult:
    status: str
    artifact_id: UUID
    receipt_id: UUID
    transformation_run_id: UUID | None
    canonical_record_id: UUID | None
    fiscal_document_id: UUID | None
    access_key: str | None
    content_hash: str
    issue_codes: tuple[str, ...]


class NFe55ImportService:
    def __init__(
        self,
        intake: DocumentIntakeService,
        parser: NFe55Parser,
        repository: FiscalDocumentRepository,
        audit: AuditService,
        *,
        id_factory: Callable[[], UUID] = uuid4,
        clock: Callable[[], datetime] | None = None,
    ) -> None:
        self._intake = intake
        self._parser = parser
        self._repository = repository
        self._audit = audit
        self._id_factory = id_factory
        self._clock = clock or (lambda: datetime.now(UTC))

    def import_xml(
        self,
        context: IntakeContext,
        request: NFe55ImportRequest,
    ) -> NFe55ImportResult:
        upload = self._intake.upload(context, UploadRequest(
            batch_id=request.batch_id,
            content=request.content,
            original_filename=request.original_filename,
            media_type='application/xml',
            classification='FISCAL_DOCUMENT_NFE55',
            channel='NFE55_IMPORT',
            external_key=request.external_key,
        ))
        try:
            parsed = self._parser.parse(request.content)
        except FiscalXmlParseError as error:
            run_id = self._quarantine_parse_error(
                context,
                upload.artifact_id,
                upload.receipt_id,
                error,
            )
            return NFe55ImportResult(
                status='QUARANTINED',
                artifact_id=upload.artifact_id,
                receipt_id=upload.receipt_id,
                transformation_run_id=run_id,
                canonical_record_id=None,
                fiscal_document_id=None,
                access_key=None,
                content_hash=upload.content_hash,
                issue_codes=(error.code,),
            )

        self._intake.require_access(context)
        fingerprint = _canonical_fingerprint(parsed)
        existing = self._repository.find_by_access_key(
            context.tenant_id,
            context.company_id,
            parsed.access_key,
        )
        if existing is not None:
            document, canonical = existing
            if canonical.source_hash == upload.content_hash:
                self._link_receipt_to_run(
                    context,
                    upload.receipt_id,
                    canonical.transformation_run_id,
                    relation='REDELIVERY_REUSED',
                )
                return NFe55ImportResult(
                    status='IDEMPOTENT_REDELIVERY',
                    artifact_id=upload.artifact_id,
                    receipt_id=upload.receipt_id,
                    transformation_run_id=canonical.transformation_run_id,
                    canonical_record_id=canonical.id,
                    fiscal_document_id=document.id,
                    access_key=document.access_key,
                    content_hash=upload.content_hash,
                    issue_codes=(),
                )
            return self._quarantine_conflict(
                context,
                parsed,
                upload.artifact_id,
                upload.receipt_id,
                upload.content_hash,
                fingerprint,
                existing_document_id=document.id,
            )

        if any(issue.severity == 'ERROR' for issue in parsed.issues):
            return self._quarantine_validation(
                context,
                parsed,
                upload.artifact_id,
                upload.receipt_id,
                upload.content_hash,
                fingerprint,
            )

        run = self._intake.record_transformation(context, TransformationRequest(
            artifact_id=upload.artifact_id,
            previous_run_id=None,
            parser_name=self._parser.parser_name,
            parser_version=self._parser.parser_version,
            schema_version=parsed.schema_version,
            output_hash=fingerprint,
            status='COMPLETED',
        ))
        self._link_receipt_to_run(
            context,
            upload.receipt_id,
            run.id,
            relation='PROCESSED_BY',
        )
        now = self._now()
        canonical_id = self._id_factory()
        document_id = self._id_factory()
        canonical = CanonicalRecord(
            id=canonical_id,
            tenant_id=context.tenant_id,
            company_id=context.company_id,
            artifact_id=upload.artifact_id,
            transformation_run_id=run.id,
            record_type='FISCAL_DOCUMENT_NFE55',
            schema_version=CANONICAL_SCHEMA_VERSION,
            external_identity=parsed.access_key,
            source_hash=upload.content_hash,
            fingerprint=fingerprint,
            fact_at=parsed.issued_at,
            status='STRUCTURALLY_VALIDATED',
            created_at=now,
        )
        document = _document(
            parsed,
            context,
            canonical_id,
            document_id,
            upload.artifact_id,
            now,
        )
        items, taxes = self._items(parsed, context, document_id, now)
        self._repository.add_document(canonical, document, items, taxes)
        for issue in parsed.issues:
            self._record_issue(context, run.id, parsed.schema_version, issue)
        self._intake.add_lineage(context, LineageRequest(
            source_type='TransformationRun',
            source_id=run.id,
            source_version=None,
            target_type='CanonicalRecord',
            target_id=canonical.id,
            target_version=1,
            transformation_run_id=run.id,
            relation='NORMALIZED_TO',
        ))
        self._intake.add_lineage(context, LineageRequest(
            source_type='CanonicalRecord',
            source_id=canonical.id,
            source_version=1,
            target_type='FiscalDocument',
            target_id=document.id,
            target_version=1,
            transformation_run_id=run.id,
            relation='TYPED_AS',
        ))
        self._record_audit(context, canonical, document, len(items), len(taxes))
        return NFe55ImportResult(
            status='IMPORTED',
            artifact_id=upload.artifact_id,
            receipt_id=upload.receipt_id,
            transformation_run_id=run.id,
            canonical_record_id=canonical.id,
            fiscal_document_id=document.id,
            access_key=document.access_key,
            content_hash=upload.content_hash,
            issue_codes=tuple(issue.code for issue in parsed.issues),
        )

    def _quarantine_parse_error(
        self,
        context: IntakeContext,
        artifact_id: UUID,
        receipt_id: UUID,
        error: FiscalXmlParseError,
    ) -> UUID:
        run = self._intake.record_transformation(context, TransformationRequest(
            artifact_id=artifact_id,
            previous_run_id=None,
            parser_name=self._parser.parser_name,
            parser_version=self._parser.parser_version,
            schema_version=error.schema_version,
            output_hash=None,
            status='FAILED',
        ))
        self._link_receipt_to_run(
            context,
            receipt_id,
            run.id,
            relation='PROCESSING_FAILED',
        )
        self._intake.add_validation_issue(context, ValidationIssueRequest(
            transformation_run_id=run.id,
            code=error.code,
            severity='ERROR',
            field_path=None,
            rule_reference=error.schema_version,
            message=str(error),
            resolution_status='QUARANTINED',
        ))
        return run.id

    def _quarantine_conflict(
        self,
        context: IntakeContext,
        parsed: ParsedNFe55,
        artifact_id: UUID,
        receipt_id: UUID,
        content_hash: str,
        fingerprint: str,
        *,
        existing_document_id: UUID,
    ) -> NFe55ImportResult:
        run = self._failed_run(context, parsed, artifact_id, fingerprint)
        self._link_receipt_to_run(
            context,
            receipt_id,
            run.id,
            relation='PROCESSING_FAILED',
        )
        code = 'NFE_ACCESS_KEY_HASH_CONFLICT'
        self._intake.add_validation_issue(context, ValidationIssueRequest(
            transformation_run_id=run.id,
            code=code,
            severity='ERROR',
            field_path='access_key',
            rule_reference=parsed.schema_version,
            message='mesma chave NF-e recebida com conteúdo diferente',
            resolution_status='QUARANTINED',
        ))
        self._intake.add_lineage(context, LineageRequest(
            source_type='TransformationRun',
            source_id=run.id,
            source_version=None,
            target_type='FiscalDocument',
            target_id=existing_document_id,
            target_version=1,
            transformation_run_id=run.id,
            relation='CONFLICTS_WITH',
        ))
        return NFe55ImportResult(
            status='CONFLICT_QUARANTINED',
            artifact_id=artifact_id,
            receipt_id=receipt_id,
            transformation_run_id=run.id,
            canonical_record_id=None,
            fiscal_document_id=existing_document_id,
            access_key=parsed.access_key,
            content_hash=content_hash,
            issue_codes=(code,),
        )

    def _quarantine_validation(
        self,
        context: IntakeContext,
        parsed: ParsedNFe55,
        artifact_id: UUID,
        receipt_id: UUID,
        content_hash: str,
        fingerprint: str,
    ) -> NFe55ImportResult:
        run = self._failed_run(context, parsed, artifact_id, fingerprint)
        self._link_receipt_to_run(
            context,
            receipt_id,
            run.id,
            relation='PROCESSING_FAILED',
        )
        for issue in parsed.issues:
            self._record_issue(context, run.id, parsed.schema_version, issue)
        return NFe55ImportResult(
            status='QUARANTINED',
            artifact_id=artifact_id,
            receipt_id=receipt_id,
            transformation_run_id=run.id,
            canonical_record_id=None,
            fiscal_document_id=None,
            access_key=parsed.access_key,
            content_hash=content_hash,
            issue_codes=tuple(issue.code for issue in parsed.issues),
        )

    def _failed_run(
        self,
        context: IntakeContext,
        parsed: ParsedNFe55,
        artifact_id: UUID,
        fingerprint: str,
    ) -> TransformationRun:
        return self._intake.record_transformation(context, TransformationRequest(
            artifact_id=artifact_id,
            previous_run_id=None,
            parser_name=self._parser.parser_name,
            parser_version=self._parser.parser_version,
            schema_version=parsed.schema_version,
            output_hash=fingerprint,
            status='FAILED',
        ))

    def _record_issue(
        self,
        context: IntakeContext,
        run_id: UUID,
        schema_version: str,
        issue: ParsedValidationIssue,
    ) -> None:
        self._intake.add_validation_issue(context, ValidationIssueRequest(
            transformation_run_id=run_id,
            code=issue.code,
            severity=issue.severity,
            field_path=issue.field_path,
            rule_reference=schema_version,
            message=issue.message,
            resolution_status='OPEN',
        ))

    def _link_receipt_to_run(
        self,
        context: IntakeContext,
        receipt_id: UUID,
        run_id: UUID,
        *,
        relation: str,
    ) -> None:
        self._intake.add_lineage(context, LineageRequest(
            source_type='ArtifactReceipt',
            source_id=receipt_id,
            source_version=None,
            target_type='TransformationRun',
            target_id=run_id,
            target_version=None,
            transformation_run_id=run_id,
            relation=relation,
        ))

    def _items(
        self,
        parsed: ParsedNFe55,
        context: IntakeContext,
        document_id: UUID,
        now: datetime,
    ) -> tuple[tuple[FiscalDocumentItem, ...], tuple[TaxDetail, ...]]:
        items: list[FiscalDocumentItem] = []
        taxes: list[TaxDetail] = []
        for parsed_item in parsed.items:
            item_id = self._id_factory()
            items.append(FiscalDocumentItem(
                id=item_id,
                tenant_id=context.tenant_id,
                company_id=context.company_id,
                fiscal_document_id=document_id,
                sequence=parsed_item.sequence,
                product_code=parsed_item.product_code,
                description=parsed_item.description,
                ncm=parsed_item.ncm,
                cfop=parsed_item.cfop,
                commercial_unit=parsed_item.commercial_unit,
                quantity=parsed_item.quantity,
                unit_value=parsed_item.unit_value,
                gross_total=parsed_item.gross_total,
                discount_total=parsed_item.discount_total,
                other_total=parsed_item.other_total,
                included_in_total=parsed_item.included_in_total,
                created_at=now,
            ))
            taxes.extend(
                TaxDetail(
                    id=self._id_factory(),
                    tenant_id=context.tenant_id,
                    company_id=context.company_id,
                    fiscal_document_item_id=item_id,
                    tax_type=tax.tax_type,
                    tax_status=tax.tax_status,
                    calculation_base=tax.calculation_base,
                    rate=tax.rate,
                    amount=tax.amount,
                    created_at=now,
                )
                for tax in parsed_item.taxes
            )
        return tuple(items), tuple(taxes)

    def _record_audit(
        self,
        context: IntakeContext,
        canonical: CanonicalRecord,
        document: FiscalDocument,
        item_count: int,
        tax_count: int,
    ) -> None:
        self._audit.record(AuditRecord(
            tenant_id=context.tenant_id,
            company_id=context.company_id,
            actor_id=context.actor_id,
            origin=context.origin,
            module='fiscal_documents',
            action='nfe55.imported',
            subject_type='FiscalDocument',
            subject_id=document.id,
            subject_version=1,
            before=None,
            after={
                'canonical_record_id': canonical.id,
                'access_key': document.access_key,
                'model': document.model,
                'schema_version': document.schema_version,
                'source_hash': canonical.source_hash,
                'fingerprint': canonical.fingerprint,
                'item_count': item_count,
                'tax_count': tax_count,
                'observed_status': document.observed_status,
            },
            reason=None,
            correlation_id=context.correlation_id,
            causation_id=context.causation_id,
        ))

    def _now(self) -> datetime:
        value = self._clock()
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError('relógio deve retornar datetime com timezone')
        return value.astimezone(UTC)


def _document(
    parsed: ParsedNFe55,
    context: IntakeContext,
    canonical_id: UUID,
    document_id: UUID,
    artifact_id: UUID,
    now: datetime,
) -> FiscalDocument:
    return FiscalDocument(
        id=document_id,
        tenant_id=context.tenant_id,
        company_id=context.company_id,
        canonical_record_id=canonical_id,
        artifact_id=artifact_id,
        access_key=parsed.access_key,
        model=parsed.model,
        schema_version=parsed.schema_version,
        series=parsed.series,
        document_number=parsed.document_number,
        operation_nature=parsed.operation_nature,
        issuer_tax_id=parsed.issuer_tax_id,
        issuer_name=parsed.issuer_name,
        recipient_tax_id=parsed.recipient_tax_id,
        recipient_name=parsed.recipient_name,
        issued_at=parsed.issued_at,
        movement_at=parsed.movement_at,
        products_total=parsed.products_total,
        freight_total=parsed.freight_total,
        insurance_total=parsed.insurance_total,
        discount_total=parsed.discount_total,
        other_total=parsed.other_total,
        tax_total=parsed.tax_total,
        invoice_total=parsed.invoice_total,
        observed_status=parsed.observed_status,
        protocol_status_code=parsed.protocol_status_code,
        protocol_status_reason=parsed.protocol_status_reason,
        created_at=now,
    )


def _canonical_fingerprint(parsed: ParsedNFe55) -> str:
    payload = asdict(parsed)
    payload.pop('issues', None)
    encoded = json.dumps(
        _json_value(payload),
        ensure_ascii=False,
        sort_keys=True,
        separators=(',', ':'),
    ).encode('utf-8')
    return sha256(encoded).hexdigest()


def _json_value(value: object) -> object:
    if isinstance(value, dict):
        return {str(key): _json_value(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_value(item) for item in value]
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, datetime):
        return value.isoformat()
    return value
