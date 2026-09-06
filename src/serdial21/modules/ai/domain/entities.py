'''Modelo de IA versionado e saída estruturada, sem operações privilegiadas.'''

from dataclasses import dataclass
from decimal import Decimal
from enum import StrEnum
from uuid import UUID


class AIPurpose(StrEnum):
    CLASSIFY = 'CLASSIFY'
    SUGGEST_ACCOUNT = 'SUGGEST_ACCOUNT'
    EXPLAIN_RULE = 'EXPLAIN_RULE'
    IDENTIFY_INCONSISTENCY = 'IDENTIFY_INCONSISTENCY'
    SUPPORT_EXCEPTION = 'SUPPORT_EXCEPTION'


class InferenceStatus(StrEnum):
    VALIDATED = 'VALIDATED'
    SUGGESTION = 'SUGGESTION'
    PENDING = 'PENDING'
    CONFLICT = 'CONFLICT'
    BLOCKED = 'BLOCKED'


@dataclass(frozen=True, slots=True)
class AIModelProfileVersion:
    id: UUID
    tenant_id: UUID
    company_id: UUID
    version: int
    model_identifier: str
    allowed_purposes: tuple[AIPurpose, ...]
    status: str


@dataclass(frozen=True, slots=True)
class PromptTemplateVersion:
    id: UUID
    profile_version_id: UUID
    version: int
    template_hash: str
    status: str


@dataclass(frozen=True, slots=True)
class AIInferenceRun:
    id: UUID
    tenant_id: UUID
    company_id: UUID
    profile_version_id: UUID
    prompt_template_version_id: UUID
    purpose: AIPurpose
    input_manifest_hash: str
    permitted_source_ids: tuple[UUID, ...]
    status: InferenceStatus
    result: 'StructuredSuggestion | None'
    confidence: Decimal | None
    error_code: str | None


@dataclass(frozen=True, slots=True)
class DecisionExplanation:
    id: UUID
    inference_run_id: UUID
    reason_codes: tuple[str, ...]
    source_ids: tuple[UUID, ...]


@dataclass(frozen=True, slots=True)
class SuggestionOutcome:
    id: UUID
    inference_run_id: UUID
    status: InferenceStatus
    reason: str | None


@dataclass(frozen=True, slots=True)
class StructuredSuggestion:
    classification: str | None
    account_version_id: UUID | None
    reason_codes: tuple[str, ...]
    confidence: Decimal


@dataclass(frozen=True, slots=True)
class InferenceInput:
    '''Dados minimizados; nunca XML/OFX/CSV bruto, segredo ou prompt completo.'''

    facts: dict[str, str | int | bool | Decimal | None]
    source_ids: tuple[UUID, ...]
