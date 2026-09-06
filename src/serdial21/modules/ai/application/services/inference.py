'''Orquestra inferência assistiva; o resultado nunca efetiva uma decisão.'''

from dataclasses import dataclass
from decimal import Decimal
from hashlib import sha256
import json
import re
from typing import Callable
from uuid import UUID, uuid4

from serdial21.modules.ai.application.ports.gateway import (
    AIGateway,
    AccountVersionLookup,
    ModelUnavailableError,
)
from serdial21.modules.ai.domain.entities import (
    AIInferenceRun,
    AIModelProfileVersion,
    AIPurpose,
    InferenceInput,
    InferenceStatus,
    PromptTemplateVersion,
    StructuredSuggestion,
)


MIN_CONFIDENCE = Decimal('0.70')
_PROHIBITED_FACT_KEY = re.compile(r'(password|secret|token|credential|api[_-]?key|xml|ofx|csv|prompt|document)', re.I)
_PROMPT_INJECTION = re.compile(r'(ignore\s+(all\s+)?(previous|prior)|system\s+prompt|you\s+are\s+now|follow\s+these\s+instructions)', re.I)


@dataclass(frozen=True, slots=True)
class InferenceRequest:
    profile: AIModelProfileVersion
    template: PromptTemplateVersion
    purpose: AIPurpose
    inference_input: InferenceInput


class AIInferenceService:
    def __init__(self, gateway: AIGateway, accounts: AccountVersionLookup,
                 *, id_factory: Callable[[], UUID] = uuid4) -> None:
        self._gateway = gateway
        self._accounts = accounts
        self._id_factory = id_factory

    def infer(self, request: InferenceRequest) -> AIInferenceRun:
        self._validate_request(request)
        manifest_hash = _manifest_hash(request.inference_input)
        blocked = _document_injection(request.inference_input)
        if blocked:
            return self._run(request, manifest_hash, InferenceStatus.BLOCKED, None,
                             None, 'PROMPT_INJECTION_DETECTED')
        try:
            suggestion = self._gateway.infer(
                profile_version_id=request.profile.id, template_version_id=request.template.id,
                purpose=request.purpose.value, inference_input=request.inference_input,
            )
        except TimeoutError:
            return self._run(request, manifest_hash, InferenceStatus.PENDING, None,
                             None, 'MODEL_TIMEOUT')
        except ModelUnavailableError:
            return self._run(request, manifest_hash, InferenceStatus.PENDING, None,
                             None, 'MODEL_UNAVAILABLE')
        status, error = self._validate_suggestion(request, suggestion)
        return self._run(request, manifest_hash, status,
                         suggestion if status is InferenceStatus.SUGGESTION else None,
                         suggestion.confidence if isinstance(suggestion, StructuredSuggestion) else None,
                         error)

    def _validate_request(self, request: InferenceRequest) -> None:
        if request.profile.status != 'PUBLISHED' or request.template.status != 'PUBLISHED':
            raise ValueError('perfil e template de IA devem estar publicados')
        if request.template.profile_version_id != request.profile.id:
            raise ValueError('template não pertence ao profile informado')
        if request.purpose not in request.profile.allowed_purposes:
            raise PermissionError('finalidade de IA não autorizada no profile')
        if not request.inference_input.source_ids:
            raise ValueError('inferência exige fontes permitidas')
        for key, value in request.inference_input.facts.items():
            if _PROHIBITED_FACT_KEY.search(key):
                raise ValueError('entrada de IA contém campo não permitido')
            if not isinstance(value, (str, int, bool, Decimal, type(None))):
                raise TypeError('entrada de IA possui tipo não permitido')

    def _validate_suggestion(self, request: InferenceRequest,
                             suggestion: object) -> tuple[InferenceStatus, str | None]:
        if not isinstance(suggestion, StructuredSuggestion):
            return InferenceStatus.BLOCKED, 'INVALID_STRUCTURED_OUTPUT'
        if not suggestion.reason_codes or any(not code.strip() for code in suggestion.reason_codes):
            return InferenceStatus.BLOCKED, 'INVALID_STRUCTURED_OUTPUT'
        if not isinstance(suggestion.confidence, Decimal) or not Decimal('0') <= suggestion.confidence <= Decimal('1'):
            return InferenceStatus.BLOCKED, 'INVALID_CONFIDENCE'
        if suggestion.confidence < MIN_CONFIDENCE:
            return InferenceStatus.PENDING, 'LOW_CONFIDENCE'
        if request.purpose is AIPurpose.SUGGEST_ACCOUNT:
            if suggestion.account_version_id is None or not self._accounts.exists_for_scope(
                request.profile.tenant_id, request.profile.company_id, suggestion.account_version_id,
            ):
                return InferenceStatus.CONFLICT, 'ACCOUNT_VERSION_NOT_FOUND'
        return InferenceStatus.SUGGESTION, None

    def _run(self, request: InferenceRequest, manifest_hash: str, status: InferenceStatus,
             result: StructuredSuggestion | None, confidence: Decimal | None,
             error: str | None) -> AIInferenceRun:
        return AIInferenceRun(
            self._id_factory(), request.profile.tenant_id, request.profile.company_id,
            request.profile.id, request.template.id, request.purpose, manifest_hash,
            request.inference_input.source_ids, status, result, confidence, error,
        )


def _document_injection(inference_input: InferenceInput) -> bool:
    return any(isinstance(value, str) and _PROMPT_INJECTION.search(value)
               for value in inference_input.facts.values())


def _manifest_hash(inference_input: InferenceInput) -> str:
    payload = {
        'facts': {key: str(value) for key, value in sorted(inference_input.facts.items())},
        'source_ids': sorted(str(source) for source in inference_input.source_ids),
    }
    return sha256(json.dumps(payload, separators=(',', ':'), sort_keys=True).encode()).hexdigest()
