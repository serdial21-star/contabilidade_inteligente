'''Gateway externo sem métodos de aprovação, exportação ou mutação.'''

from typing import Protocol
from uuid import UUID

from serdial21.modules.ai.domain.entities import InferenceInput, StructuredSuggestion


class ModelUnavailableError(RuntimeError):
    '''O provedor não está disponível; o fluxo seguro deve continuar pendente.'''


class AIGateway(Protocol):
    def infer(self, *, profile_version_id: UUID, template_version_id: UUID,
              purpose: str, inference_input: InferenceInput) -> StructuredSuggestion: ...


class AccountVersionLookup(Protocol):
    def exists_for_scope(self, tenant_id: UUID, company_id: UUID,
                         account_version_id: UUID) -> bool: ...
