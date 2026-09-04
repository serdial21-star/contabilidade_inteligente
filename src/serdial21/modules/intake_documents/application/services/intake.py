'''Casos de uso da fundação documental, sem parser fiscal.'''

from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime
from hashlib import sha256
from pathlib import PurePath
from uuid import UUID, uuid4

from serdial21.modules.audit.application.services.audit import AuditRecord, AuditService
from serdial21.modules.audit.domain.entities import AuditOrigin
from serdial21.modules.intake_documents.application.ports.object_storage import (
    ObjectStorage,
)
from serdial21.modules.intake_documents.application.ports.authorization import (
    DocumentAuthorization,
)
from serdial21.modules.intake_documents.application.ports.repository import (
    IntakeRepository,
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


class IntakeResourceUnavailableError(LookupError):
    '''Negação uniforme para recurso ausente ou fora do escopo.'''


class InvalidLineageError(ValueError):
    '''Indica auto-referência ou ciclo na linhagem.'''


@dataclass(frozen=True, slots=True)
class IntakeContext:
    tenant_id: UUID
    company_id: UUID
    actor_id: UUID | None
    origin: AuditOrigin
    correlation_id: UUID
    causation_id: UUID | None = None


@dataclass(frozen=True, slots=True)
class StartBatchRequest:
    source: str
    idempotency_key: str


@dataclass(frozen=True, slots=True)
class UploadRequest:
    batch_id: UUID
    content: bytes
    original_filename: str
    media_type: str
    classification: str
    channel: str
    external_key: str | None = None


@dataclass(frozen=True, slots=True)
class UploadResult:
    artifact_id: UUID
    receipt_id: UUID
    import_item_id: UUID
    content_hash: str
    storage_key: str
    duplicate: bool


@dataclass(frozen=True, slots=True)
class TransformationRequest:
    artifact_id: UUID
    previous_run_id: UUID | None
    parser_name: str
    parser_version: str
    schema_version: str | None
    output_hash: str | None
    status: str


@dataclass(frozen=True, slots=True)
class ValidationIssueRequest:
    transformation_run_id: UUID
    code: str
    severity: str
    field_path: str | None
    rule_reference: str | None
    message: str
    resolution_status: str = 'OPEN'


@dataclass(frozen=True, slots=True)
class LineageRequest:
    source_type: str
    source_id: UUID
    source_version: int | None
    target_type: str
    target_id: UUID
    target_version: int | None
    transformation_run_id: UUID | None
    relation: str


class DocumentIntakeService:
    def __init__(
        self,
        repository: IntakeRepository,
        storage: ObjectStorage,
        audit: AuditService,
        authorization: DocumentAuthorization,
        *,
        id_factory: Callable[[], UUID] = uuid4,
        clock: Callable[[], datetime] | None = None,
    ) -> None:
        self._repository = repository
        self._storage = storage
        self._audit = audit
        self._authorization = authorization
        self._id_factory = id_factory
        self._clock = clock or (lambda: datetime.now(UTC))

    def start_batch(
        self,
        context: IntakeContext,
        request: StartBatchRequest,
    ) -> ImportBatch:
        self._authorize(context)
        if not request.source.strip() or not request.idempotency_key.strip():
            raise ValueError('origem e chave de idempotência são obrigatórias')
        existing = self._repository.find_batch_by_idempotency(
            context.tenant_id,
            context.company_id,
            request.source,
            request.idempotency_key,
        )
        if existing is not None:
            return existing
        now = self._now()
        batch = ImportBatch(
            id=self._id_factory(),
            tenant_id=context.tenant_id,
            company_id=context.company_id,
            source=request.source,
            idempotency_key=request.idempotency_key,
            status='RECEIVED',
            total_items=0,
            received_items=0,
            duplicate_items=0,
            failed_items=0,
            started_at=now,
            completed_at=None,
            revision=1,
        )
        self._repository.add_batch(batch)
        self._record(context, 'import_batch.created', 'ImportBatch', batch.id, {
            'source': batch.source,
            'status': batch.status,
        })
        return batch

    def upload(
        self,
        context: IntakeContext,
        request: UploadRequest,
    ) -> UploadResult:
        self._authorize(context)
        if PurePath(request.original_filename).name != request.original_filename:
            raise ValueError('nome de arquivo não pode conter caminho')
        if not request.original_filename or len(request.original_filename) > 255:
            raise ValueError('nome de arquivo inválido')
        if not request.media_type.strip() or not request.classification.strip():
            raise ValueError('mídia e classificação são obrigatórias')

        content_hash = sha256(request.content).hexdigest()
        storage_key = _storage_key(context.tenant_id, content_hash)
        stored = self._storage.put_if_absent(
            storage_key,
            request.content,
            expected_hash=content_hash,
        )

        batch = self._repository.get_batch(
            context.tenant_id,
            context.company_id,
            request.batch_id,
        )
        if batch is None:
            raise IntakeResourceUnavailableError('resource unavailable')

        artifact = self._repository.find_artifact_by_hash(
            context.tenant_id,
            content_hash,
        )
        duplicate = artifact is not None
        now = self._now()
        if artifact is None:
            artifact = EvidenceArtifact(
                id=self._id_factory(),
                tenant_id=context.tenant_id,
                content_hash=content_hash,
                hash_algorithm='SHA-256',
                storage_key=stored.key,
                media_type=request.media_type,
                size_bytes=stored.size_bytes,
                classification=request.classification,
                captured_at=now,
                verified_at=now,
            )
            self._repository.add_artifact(artifact)
            self._record(
                context,
                'evidence_artifact.created',
                'EvidenceArtifact',
                artifact.id,
                {
                    'content_hash': artifact.content_hash,
                    'media_type': artifact.media_type,
                    'size_bytes': artifact.size_bytes,
                    'classification': artifact.classification,
                },
            )

        receipt = ArtifactReceipt(
            id=self._id_factory(),
            tenant_id=context.tenant_id,
            company_id=context.company_id,
            batch_id=batch.id,
            artifact_id=artifact.id,
            original_filename=request.original_filename,
            channel=request.channel,
            external_key=request.external_key,
            result='DUPLICATE' if duplicate else 'ACCEPTED',
            received_at=now,
        )
        sequence = self._repository.next_item_sequence(
            context.tenant_id,
            context.company_id,
            batch.id,
        )
        item = ImportItem(
            id=self._id_factory(),
            tenant_id=context.tenant_id,
            company_id=context.company_id,
            batch_id=batch.id,
            receipt_id=receipt.id,
            sequence=sequence,
            status=receipt.result,
            error_code=None,
            created_subject_type='EvidenceArtifact',
            created_subject_id=artifact.id,
            created_at=now,
        )
        self._repository.add_receipt(receipt)
        self._repository.add_item(item)
        self._repository.register_batch_item(
            context.tenant_id,
            context.company_id,
            batch.id,
            duplicate=duplicate,
        )
        self._record(
            context,
            'artifact_receipt.created',
            'ArtifactReceipt',
            receipt.id,
            {
                'artifact_id': artifact.id,
                'batch_id': batch.id,
                'channel': receipt.channel,
                'result': receipt.result,
            },
        )
        return UploadResult(
            artifact_id=artifact.id,
            receipt_id=receipt.id,
            import_item_id=item.id,
            content_hash=content_hash,
            storage_key=storage_key,
            duplicate=duplicate,
        )

    def record_transformation(
        self,
        context: IntakeContext,
        request: TransformationRequest,
    ) -> TransformationRun:
        self._authorize(context)
        if request.status not in {'STARTED', 'COMPLETED', 'FAILED'}:
            raise ValueError('status de transformação inválido')
        if not request.parser_name.strip() or not request.parser_version.strip():
            raise ValueError('parser e versão são obrigatórios')
        if request.output_hash is not None and not _is_sha256(request.output_hash):
            raise ValueError('hash de saída inválido')
        artifact = self._repository.get_artifact(
            context.tenant_id,
            request.artifact_id,
        )
        if artifact is None or not self._repository.company_has_receipt(
            context.tenant_id,
            context.company_id,
            request.artifact_id,
        ):
            raise IntakeResourceUnavailableError('resource unavailable')
        if request.previous_run_id is not None and self._repository.get_transformation(
            context.tenant_id,
            context.company_id,
            request.previous_run_id,
        ) is None:
            raise IntakeResourceUnavailableError('resource unavailable')

        now = self._now()
        run = TransformationRun(
            id=self._id_factory(),
            tenant_id=context.tenant_id,
            company_id=context.company_id,
            artifact_id=artifact.id,
            previous_run_id=request.previous_run_id,
            parser_name=request.parser_name,
            parser_version=request.parser_version,
            schema_version=request.schema_version,
            input_hash=artifact.content_hash,
            output_hash=request.output_hash,
            status=request.status,
            started_at=now,
            completed_at=now if request.status in {'COMPLETED', 'FAILED'} else None,
        )
        self._repository.add_transformation(run)
        self._record(
            context,
            'transformation_run.created',
            'TransformationRun',
            run.id,
            {
                'artifact_id': artifact.id,
                'parser_name': run.parser_name,
                'parser_version': run.parser_version,
                'input_hash': run.input_hash,
                'output_hash': run.output_hash,
                'status': run.status,
            },
        )
        self.add_lineage(context, LineageRequest(
            source_type='EvidenceArtifact',
            source_id=artifact.id,
            source_version=None,
            target_type='TransformationRun',
            target_id=run.id,
            target_version=None,
            transformation_run_id=run.id,
            relation='TRANSFORMED_BY',
        ))
        return run

    def add_validation_issue(
        self,
        context: IntakeContext,
        request: ValidationIssueRequest,
    ) -> ValidationIssue:
        self._authorize(context)
        if not request.code.strip() or not request.severity.strip():
            raise ValueError('código e severidade são obrigatórios')
        if self._repository.get_transformation(
            context.tenant_id,
            context.company_id,
            request.transformation_run_id,
        ) is None:
            raise IntakeResourceUnavailableError('resource unavailable')
        issue = ValidationIssue(
            id=self._id_factory(),
            tenant_id=context.tenant_id,
            company_id=context.company_id,
            transformation_run_id=request.transformation_run_id,
            code=request.code,
            severity=request.severity,
            field_path=request.field_path,
            rule_reference=request.rule_reference,
            message=request.message,
            resolution_status=request.resolution_status,
            created_at=self._now(),
        )
        self._repository.add_validation_issue(issue)
        self._record(
            context,
            'validation_issue.created',
            'ValidationIssue',
            issue.id,
            {
                'transformation_run_id': issue.transformation_run_id,
                'code': issue.code,
                'severity': issue.severity,
                'field_path': issue.field_path,
                'resolution_status': issue.resolution_status,
            },
        )
        return issue

    def add_lineage(
        self,
        context: IntakeContext,
        request: LineageRequest,
    ) -> LineageEdge:
        self._authorize(context)
        if request.transformation_run_id is not None:
            run = self._repository.get_transformation(
                context.tenant_id,
                context.company_id,
                request.transformation_run_id,
            )
            if run is None:
                raise IntakeResourceUnavailableError('resource unavailable')
        if self._repository.lineage_path_exists(
            context.tenant_id,
            context.company_id,
            request.target_type,
            request.target_id,
            request.source_type,
            request.source_id,
        ):
            raise InvalidLineageError('linhagem cíclica não é permitida')
        edge = LineageEdge(
            id=self._id_factory(),
            tenant_id=context.tenant_id,
            company_id=context.company_id,
            source_type=request.source_type,
            source_id=request.source_id,
            source_version=request.source_version,
            target_type=request.target_type,
            target_id=request.target_id,
            target_version=request.target_version,
            transformation_run_id=request.transformation_run_id,
            relation=request.relation,
            created_at=self._now(),
        )
        self._repository.add_lineage(edge)
        self._record(
            context,
            'lineage_edge.created',
            'LineageEdge',
            edge.id,
            {
                'source_type': edge.source_type,
                'source_id': edge.source_id,
                'target_type': edge.target_type,
                'target_id': edge.target_id,
                'relation': edge.relation,
            },
        )
        return edge

    def _now(self) -> datetime:
        value = self._clock()
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError('relógio deve retornar datetime com timezone')
        return value.astimezone(UTC)

    def _authorize(self, context: IntakeContext) -> None:
        self._authorization.require_company_manage(
            context.tenant_id,
            context.company_id,
            context.actor_id,
            at=self._now(),
        )

    def _record(
        self,
        context: IntakeContext,
        action: str,
        subject_type: str,
        subject_id: UUID,
        after: dict[str, object],
    ) -> None:
        self._audit.record(AuditRecord(
            tenant_id=context.tenant_id,
            company_id=context.company_id,
            actor_id=context.actor_id,
            origin=context.origin,
            module='intake_documents',
            action=action,
            subject_type=subject_type,
            subject_id=subject_id,
            subject_version=None,
            before=None,
            after=after,
            reason=None,
            correlation_id=context.correlation_id,
            causation_id=context.causation_id,
        ))


def _storage_key(tenant_id: UUID, content_hash: str) -> str:
    return f'{tenant_id}/{content_hash[:2]}/{content_hash}'


def _is_sha256(value: str) -> bool:
    return len(value) == 64 and all(character in '0123456789abcdef' for character in value)
