'''Repositório SQLAlchemy dos metadados documentais.'''

from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from serdial21.modules.intake_documents.adapters.outbound.persistence.models import (
    ArtifactReceiptModel,
    EvidenceArtifactModel,
    ImportBatchModel,
    ImportItemModel,
    LineageEdgeModel,
    TransformationRunModel,
    ValidationIssueModel,
)
from serdial21.modules.intake_documents.domain.entities import (
    ArtifactReceipt,
    EvidenceArtifact,
    ImportBatch,
    ImportItem,
    LineageEdge,
    TransformationRun,
    ValidationIssue,
)


class SqlAlchemyIntakeRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def add_batch(self, batch: ImportBatch) -> None:
        self._session.add(ImportBatchModel(
            id=batch.id,
            tenant_id=batch.tenant_id,
            company_id=batch.company_id,
            source=batch.source,
            idempotency_key=batch.idempotency_key,
            status=batch.status,
            total_items=batch.total_items,
            received_items=batch.received_items,
            duplicate_items=batch.duplicate_items,
            failed_items=batch.failed_items,
            started_at=batch.started_at,
            completed_at=batch.completed_at,
            revision=batch.revision,
        ))

    def get_batch(
        self,
        tenant_id: UUID,
        company_id: UUID,
        batch_id: UUID,
    ) -> ImportBatch | None:
        for pending in self._session.new:
            if (
                isinstance(pending, ImportBatchModel)
                and pending.tenant_id == tenant_id
                and pending.company_id == company_id
                and pending.id == batch_id
            ):
                return _batch(pending)
        model = self._session.scalar(select(ImportBatchModel).where(
            ImportBatchModel.tenant_id == tenant_id,
            ImportBatchModel.company_id == company_id,
            ImportBatchModel.id == batch_id,
        ))
        return None if model is None else _batch(model)

    def find_batch_by_idempotency(
        self,
        tenant_id: UUID,
        company_id: UUID,
        source: str,
        idempotency_key: str,
    ) -> ImportBatch | None:
        for pending in self._session.new:
            if (
                isinstance(pending, ImportBatchModel)
                and pending.tenant_id == tenant_id
                and pending.company_id == company_id
                and pending.source == source
                and pending.idempotency_key == idempotency_key
            ):
                return _batch(pending)
        model = self._session.scalar(select(ImportBatchModel).where(
            ImportBatchModel.tenant_id == tenant_id,
            ImportBatchModel.company_id == company_id,
            ImportBatchModel.source == source,
            ImportBatchModel.idempotency_key == idempotency_key,
        ))
        return None if model is None else _batch(model)

    def add_artifact(self, artifact: EvidenceArtifact) -> None:
        self._session.add(EvidenceArtifactModel(
            id=artifact.id,
            tenant_id=artifact.tenant_id,
            content_hash=artifact.content_hash,
            hash_algorithm=artifact.hash_algorithm,
            storage_key=artifact.storage_key,
            media_type=artifact.media_type,
            size_bytes=artifact.size_bytes,
            classification=artifact.classification,
            captured_at=artifact.captured_at,
            verified_at=artifact.verified_at,
        ))

    def find_artifact_by_hash(
        self,
        tenant_id: UUID,
        content_hash: str,
    ) -> EvidenceArtifact | None:
        for pending in self._session.new:
            if (
                isinstance(pending, EvidenceArtifactModel)
                and pending.tenant_id == tenant_id
                and pending.content_hash == content_hash
            ):
                return _artifact(pending)
        model = self._session.scalar(select(EvidenceArtifactModel).where(
            EvidenceArtifactModel.tenant_id == tenant_id,
            EvidenceArtifactModel.hash_algorithm == 'SHA-256',
            EvidenceArtifactModel.content_hash == content_hash,
        ))
        return None if model is None else _artifact(model)

    def get_artifact(
        self,
        tenant_id: UUID,
        artifact_id: UUID,
    ) -> EvidenceArtifact | None:
        for pending in self._session.new:
            if (
                isinstance(pending, EvidenceArtifactModel)
                and pending.tenant_id == tenant_id
                and pending.id == artifact_id
            ):
                return _artifact(pending)
        model = self._session.scalar(select(EvidenceArtifactModel).where(
            EvidenceArtifactModel.tenant_id == tenant_id,
            EvidenceArtifactModel.id == artifact_id,
        ))
        return None if model is None else _artifact(model)

    def add_receipt(self, receipt: ArtifactReceipt) -> None:
        # Garante que batch e artefato pais existam antes do recebimento.
        self._session.flush()
        self._session.add(ArtifactReceiptModel(
            id=receipt.id,
            tenant_id=receipt.tenant_id,
            company_id=receipt.company_id,
            batch_id=receipt.batch_id,
            artifact_id=receipt.artifact_id,
            original_filename=receipt.original_filename,
            channel=receipt.channel,
            external_key=receipt.external_key,
            result=receipt.result,
            received_at=receipt.received_at,
        ))

    def company_has_receipt(
        self,
        tenant_id: UUID,
        company_id: UUID,
        artifact_id: UUID,
    ) -> bool:
        if any(
            isinstance(pending, ArtifactReceiptModel)
            and pending.tenant_id == tenant_id
            and pending.company_id == company_id
            and pending.artifact_id == artifact_id
            for pending in self._session.new
        ):
            return True
        statement = select(ArtifactReceiptModel.id).where(
            ArtifactReceiptModel.tenant_id == tenant_id,
            ArtifactReceiptModel.company_id == company_id,
            ArtifactReceiptModel.artifact_id == artifact_id,
        ).limit(1)
        return self._session.scalar(statement) is not None

    def add_item(self, item: ImportItem) -> None:
        # O item referencia o recebimento criado na mesma unidade de trabalho.
        self._session.flush()
        self._session.add(ImportItemModel(
            id=item.id,
            tenant_id=item.tenant_id,
            company_id=item.company_id,
            batch_id=item.batch_id,
            receipt_id=item.receipt_id,
            sequence=item.sequence,
            status=item.status,
            error_code=item.error_code,
            created_subject_type=item.created_subject_type,
            created_subject_id=item.created_subject_id,
            created_at=item.created_at,
        ))

    def next_item_sequence(
        self,
        tenant_id: UUID,
        company_id: UUID,
        batch_id: UUID,
    ) -> int:
        current = self._session.scalar(
            select(func.max(ImportItemModel.sequence)).where(
                ImportItemModel.tenant_id == tenant_id,
                ImportItemModel.company_id == company_id,
                ImportItemModel.batch_id == batch_id,
            )
        )
        pending_sequences = [
            pending.sequence
            for pending in self._session.new
            if isinstance(pending, ImportItemModel)
            and pending.tenant_id == tenant_id
            and pending.company_id == company_id
            and pending.batch_id == batch_id
        ]
        return max([int(current or 0), *pending_sequences]) + 1

    def register_batch_item(
        self,
        tenant_id: UUID,
        company_id: UUID,
        batch_id: UUID,
        *,
        duplicate: bool,
    ) -> None:
        model = next((
            pending
            for pending in self._session.new
            if isinstance(pending, ImportBatchModel)
            and pending.tenant_id == tenant_id
            and pending.company_id == company_id
            and pending.id == batch_id
        ), None)
        if model is None:
            model = self._session.scalar(select(ImportBatchModel).where(
                ImportBatchModel.tenant_id == tenant_id,
                ImportBatchModel.company_id == company_id,
                ImportBatchModel.id == batch_id,
            ))
        if model is None:
            raise LookupError('import batch not found')
        model.total_items += 1
        model.received_items += 1
        model.duplicate_items += int(duplicate)
        model.revision += 1

    def add_transformation(self, run: TransformationRun) -> None:
        self._session.add(TransformationRunModel(
            id=run.id,
            tenant_id=run.tenant_id,
            company_id=run.company_id,
            artifact_id=run.artifact_id,
            previous_run_id=run.previous_run_id,
            parser_name=run.parser_name,
            parser_version=run.parser_version,
            schema_version=run.schema_version,
            input_hash=run.input_hash,
            output_hash=run.output_hash,
            status=run.status,
            started_at=run.started_at,
            completed_at=run.completed_at,
        ))

    def get_transformation(
        self,
        tenant_id: UUID,
        company_id: UUID,
        run_id: UUID,
    ) -> TransformationRun | None:
        for pending in self._session.new:
            if (
                isinstance(pending, TransformationRunModel)
                and pending.tenant_id == tenant_id
                and pending.company_id == company_id
                and pending.id == run_id
            ):
                return _transformation(pending)
        model = self._session.scalar(select(TransformationRunModel).where(
            TransformationRunModel.tenant_id == tenant_id,
            TransformationRunModel.company_id == company_id,
            TransformationRunModel.id == run_id,
        ))
        return None if model is None else _transformation(model)

    def add_validation_issue(self, issue: ValidationIssue) -> None:
        self._session.flush()
        self._session.add(ValidationIssueModel(
            id=issue.id,
            tenant_id=issue.tenant_id,
            company_id=issue.company_id,
            transformation_run_id=issue.transformation_run_id,
            code=issue.code,
            severity=issue.severity,
            field_path=issue.field_path,
            rule_reference=issue.rule_reference,
            message=issue.message,
            resolution_status=issue.resolution_status,
            created_at=issue.created_at,
        ))

    def add_lineage(self, edge: LineageEdge) -> None:
        self._session.flush()
        self._session.add(LineageEdgeModel(
            id=edge.id,
            tenant_id=edge.tenant_id,
            company_id=edge.company_id,
            source_type=edge.source_type,
            source_id=edge.source_id,
            source_version=edge.source_version,
            target_type=edge.target_type,
            target_id=edge.target_id,
            target_version=edge.target_version,
            transformation_run_id=edge.transformation_run_id,
            relation=edge.relation,
            created_at=edge.created_at,
        ))

    def lineage_path_exists(
        self,
        tenant_id: UUID,
        company_id: UUID,
        source_type: str,
        source_id: UUID,
        target_type: str,
        target_id: UUID,
    ) -> bool:
        rows = self._session.scalars(select(LineageEdgeModel).where(
            LineageEdgeModel.tenant_id == tenant_id,
            LineageEdgeModel.company_id == company_id,
        ))
        adjacency: dict[tuple[str, UUID], set[tuple[str, UUID]]] = {}
        for row in rows:
            source = (row.source_type, row.source_id)
            adjacency.setdefault(source, set()).add((row.target_type, row.target_id))
        for row in self._session.new:
            if (
                isinstance(row, LineageEdgeModel)
                and row.tenant_id == tenant_id
                and row.company_id == company_id
            ):
                source = (row.source_type, row.source_id)
                adjacency.setdefault(source, set()).add(
                    (row.target_type, row.target_id)
                )
        target = (target_type, target_id)
        pending = [(source_type, source_id)]
        visited: set[tuple[str, UUID]] = set()
        while pending:
            current = pending.pop()
            if current == target:
                return True
            if current in visited:
                continue
            visited.add(current)
            pending.extend(adjacency.get(current, ()))
        return False

    def list_lineage_from(
        self,
        tenant_id: UUID,
        company_id: UUID,
        source_type: str,
        source_id: UUID,
    ) -> list[LineageEdge]:
        statement = select(LineageEdgeModel).where(
            LineageEdgeModel.tenant_id == tenant_id,
            LineageEdgeModel.company_id == company_id,
            LineageEdgeModel.source_type == source_type,
            LineageEdgeModel.source_id == source_id,
        )
        return [_lineage(model) for model in self._session.scalars(statement)]


def _batch(model: ImportBatchModel) -> ImportBatch:
    return ImportBatch(
        id=model.id,
        tenant_id=model.tenant_id,
        company_id=model.company_id,
        source=model.source,
        idempotency_key=model.idempotency_key,
        status=model.status,
        total_items=model.total_items,
        received_items=model.received_items,
        duplicate_items=model.duplicate_items,
        failed_items=model.failed_items,
        started_at=model.started_at,
        completed_at=model.completed_at,
        revision=model.revision,
    )


def _artifact(model: EvidenceArtifactModel) -> EvidenceArtifact:
    return EvidenceArtifact(
        id=model.id,
        tenant_id=model.tenant_id,
        content_hash=model.content_hash,
        hash_algorithm=model.hash_algorithm,
        storage_key=model.storage_key,
        media_type=model.media_type,
        size_bytes=model.size_bytes,
        classification=model.classification,
        captured_at=model.captured_at,
        verified_at=model.verified_at,
    )


def _transformation(model: TransformationRunModel) -> TransformationRun:
    return TransformationRun(
        id=model.id,
        tenant_id=model.tenant_id,
        company_id=model.company_id,
        artifact_id=model.artifact_id,
        previous_run_id=model.previous_run_id,
        parser_name=model.parser_name,
        parser_version=model.parser_version,
        schema_version=model.schema_version,
        input_hash=model.input_hash,
        output_hash=model.output_hash,
        status=model.status,
        started_at=model.started_at,
        completed_at=model.completed_at,
    )


def _lineage(model: LineageEdgeModel) -> LineageEdge:
    return LineageEdge(
        id=model.id,
        tenant_id=model.tenant_id,
        company_id=model.company_id,
        source_type=model.source_type,
        source_id=model.source_id,
        source_version=model.source_version,
        target_type=model.target_type,
        target_id=model.target_id,
        target_version=model.target_version,
        transformation_run_id=model.transformation_run_id,
        relation=model.relation,
        created_at=model.created_at,
    )
