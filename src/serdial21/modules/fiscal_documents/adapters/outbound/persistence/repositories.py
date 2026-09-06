'''Repositório SQLAlchemy tenant-aware de documentos fiscais.'''

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from serdial21.modules.fiscal_documents.adapters.outbound.persistence.models import (
    CanonicalRecordModel,
    FiscalDocumentItemModel,
    FiscalDocumentModel,
    TaxDetailModel,
)
from serdial21.modules.fiscal_documents.domain.entities import (
    CanonicalRecord,
    FiscalDocument,
    FiscalDocumentItem,
    TaxDetail,
)


class SqlAlchemyFiscalDocumentRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def find_by_access_key(
        self,
        tenant_id: UUID,
        company_id: UUID,
        access_key: str,
    ) -> tuple[FiscalDocument, CanonicalRecord] | None:
        pending_document = next((
            item
            for item in self._session.new
            if isinstance(item, FiscalDocumentModel)
            and item.tenant_id == tenant_id
            and item.company_id == company_id
            and item.access_key == access_key
        ), None)
        if pending_document is not None:
            pending_canonical = next((
                item
                for item in self._session.new
                if isinstance(item, CanonicalRecordModel)
                and item.tenant_id == tenant_id
                and item.company_id == company_id
                and item.id == pending_document.canonical_record_id
            ), None)
            if pending_canonical is not None:
                return _document(pending_document), _canonical(pending_canonical)

        statement = (
            select(FiscalDocumentModel, CanonicalRecordModel)
            .join(
                CanonicalRecordModel,
                (
                    CanonicalRecordModel.tenant_id == FiscalDocumentModel.tenant_id
                ) & (
                    CanonicalRecordModel.company_id == FiscalDocumentModel.company_id
                ) & (
                    CanonicalRecordModel.id == FiscalDocumentModel.canonical_record_id
                ),
            )
            .where(
                FiscalDocumentModel.tenant_id == tenant_id,
                FiscalDocumentModel.company_id == company_id,
                FiscalDocumentModel.access_key == access_key,
            )
        )
        row = self._session.execute(statement).one_or_none()
        if row is None:
            return None
        return _document(row[0]), _canonical(row[1])

    def add_document(
        self,
        canonical: CanonicalRecord,
        document: FiscalDocument,
        items: tuple[FiscalDocumentItem, ...],
        taxes: tuple[TaxDetail, ...],
    ) -> None:
        self._session.add(CanonicalRecordModel(
            id=canonical.id,
            tenant_id=canonical.tenant_id,
            company_id=canonical.company_id,
            artifact_id=canonical.artifact_id,
            transformation_run_id=canonical.transformation_run_id,
            record_type=canonical.record_type,
            schema_version=canonical.schema_version,
            external_identity=canonical.external_identity,
            source_hash=canonical.source_hash,
            fingerprint=canonical.fingerprint,
            fact_at=canonical.fact_at,
            status=canonical.status,
            created_at=canonical.created_at,
        ))
        self._session.flush()
        self._session.add(FiscalDocumentModel(
            id=document.id,
            tenant_id=document.tenant_id,
            company_id=document.company_id,
            canonical_record_id=document.canonical_record_id,
            artifact_id=document.artifact_id,
            access_key=document.access_key,
            model=document.model,
            schema_version=document.schema_version,
            series=document.series,
            document_number=document.document_number,
            operation_nature=document.operation_nature,
            issuer_tax_id=document.issuer_tax_id,
            issuer_name=document.issuer_name,
            recipient_tax_id=document.recipient_tax_id,
            recipient_name=document.recipient_name,
            issued_at=document.issued_at,
            movement_at=document.movement_at,
            products_total=document.products_total,
            freight_total=document.freight_total,
            insurance_total=document.insurance_total,
            discount_total=document.discount_total,
            other_total=document.other_total,
            tax_total=document.tax_total,
            invoice_total=document.invoice_total,
            observed_status=document.observed_status,
            protocol_status_code=document.protocol_status_code,
            protocol_status_reason=document.protocol_status_reason,
            created_at=document.created_at,
        ))
        self._session.flush()
        self._session.add_all([
            FiscalDocumentItemModel(
                id=item.id,
                tenant_id=item.tenant_id,
                company_id=item.company_id,
                fiscal_document_id=item.fiscal_document_id,
                sequence=item.sequence,
                product_code=item.product_code,
                description=item.description,
                ncm=item.ncm,
                cfop=item.cfop,
                commercial_unit=item.commercial_unit,
                quantity=item.quantity,
                unit_value=item.unit_value,
                gross_total=item.gross_total,
                discount_total=item.discount_total,
                other_total=item.other_total,
                included_in_total=item.included_in_total,
                created_at=item.created_at,
            )
            for item in items
        ])
        self._session.flush()
        self._session.add_all([
            TaxDetailModel(
                id=tax.id,
                tenant_id=tax.tenant_id,
                company_id=tax.company_id,
                fiscal_document_item_id=tax.fiscal_document_item_id,
                tax_type=tax.tax_type,
                tax_status=tax.tax_status,
                calculation_base=tax.calculation_base,
                rate=tax.rate,
                amount=tax.amount,
                created_at=tax.created_at,
            )
            for tax in taxes
        ])


def _canonical(model: CanonicalRecordModel) -> CanonicalRecord:
    return CanonicalRecord(
        id=model.id,
        tenant_id=model.tenant_id,
        company_id=model.company_id,
        artifact_id=model.artifact_id,
        transformation_run_id=model.transformation_run_id,
        record_type=model.record_type,
        schema_version=model.schema_version,
        external_identity=model.external_identity,
        source_hash=model.source_hash,
        fingerprint=model.fingerprint,
        fact_at=model.fact_at,
        status=model.status,
        created_at=model.created_at,
    )


def _document(model: FiscalDocumentModel) -> FiscalDocument:
    return FiscalDocument(
        id=model.id,
        tenant_id=model.tenant_id,
        company_id=model.company_id,
        canonical_record_id=model.canonical_record_id,
        artifact_id=model.artifact_id,
        access_key=model.access_key,
        model=model.model,
        schema_version=model.schema_version,
        series=model.series,
        document_number=model.document_number,
        operation_nature=model.operation_nature,
        issuer_tax_id=model.issuer_tax_id,
        issuer_name=model.issuer_name,
        recipient_tax_id=model.recipient_tax_id,
        recipient_name=model.recipient_name,
        issued_at=model.issued_at,
        movement_at=model.movement_at,
        products_total=model.products_total,
        freight_total=model.freight_total,
        insurance_total=model.insurance_total,
        discount_total=model.discount_total,
        other_total=model.other_total,
        tax_total=model.tax_total,
        invoice_total=model.invoice_total,
        observed_status=model.observed_status,
        protocol_status_code=model.protocol_status_code,
        protocol_status_reason=model.protocol_status_reason,
        created_at=model.created_at,
    )
