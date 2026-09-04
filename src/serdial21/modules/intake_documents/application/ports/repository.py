'''Porta tenant-aware para metadados documentais.'''

from typing import Protocol
from uuid import UUID

from serdial21.modules.intake_documents.domain.entities import (
    ArtifactReceipt,
    EvidenceArtifact,
    ImportBatch,
    ImportItem,
    LineageEdge,
    TransformationRun,
    ValidationIssue,
)


class IntakeRepository(Protocol):
    def add_batch(self, batch: ImportBatch) -> None: ...

    def get_batch(
        self,
        tenant_id: UUID,
        company_id: UUID,
        batch_id: UUID,
    ) -> ImportBatch | None: ...

    def find_batch_by_idempotency(
        self,
        tenant_id: UUID,
        company_id: UUID,
        source: str,
        idempotency_key: str,
    ) -> ImportBatch | None: ...

    def add_artifact(self, artifact: EvidenceArtifact) -> None: ...

    def find_artifact_by_hash(
        self,
        tenant_id: UUID,
        content_hash: str,
    ) -> EvidenceArtifact | None: ...

    def get_artifact(
        self,
        tenant_id: UUID,
        artifact_id: UUID,
    ) -> EvidenceArtifact | None: ...

    def add_receipt(self, receipt: ArtifactReceipt) -> None: ...

    def company_has_receipt(
        self,
        tenant_id: UUID,
        company_id: UUID,
        artifact_id: UUID,
    ) -> bool: ...

    def add_item(self, item: ImportItem) -> None: ...

    def next_item_sequence(
        self,
        tenant_id: UUID,
        company_id: UUID,
        batch_id: UUID,
    ) -> int: ...

    def register_batch_item(
        self,
        tenant_id: UUID,
        company_id: UUID,
        batch_id: UUID,
        *,
        duplicate: bool,
    ) -> None: ...

    def add_transformation(self, run: TransformationRun) -> None: ...

    def get_transformation(
        self,
        tenant_id: UUID,
        company_id: UUID,
        run_id: UUID,
    ) -> TransformationRun | None: ...

    def add_validation_issue(self, issue: ValidationIssue) -> None: ...

    def add_lineage(self, edge: LineageEdge) -> None: ...

    def lineage_path_exists(
        self,
        tenant_id: UUID,
        company_id: UUID,
        source_type: str,
        source_id: UUID,
        target_type: str,
        target_id: UUID,
    ) -> bool: ...

    def list_lineage_from(
        self,
        tenant_id: UUID,
        company_id: UUID,
        source_type: str,
        source_id: UUID,
    ) -> list[LineageEdge]: ...
