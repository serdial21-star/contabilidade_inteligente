# Accounting Automation Core

O núcleo classifica `FiscalDocumentItem`, nunca apenas o documento. A sequência é item → evidências → intenção → confiança → mapping versionado → proposta → decisão humana. A automação pode preparar proposta, mas não aprova nem escritura.

O motor determinístico existente foi estendido; não existe motor paralelo. Catálogos antigos continuam no fluxo documental legado. Estado: domínio, schema e cenários sintéticos `READY`; orquestração persistente/API/UI ainda `PARTIAL`.

## Contrato da API de revisão por item (decidido em 2026-09-21, pendente de implementação)

A fila de revisão humana de `ItemClassification` segue o padrão já existente em `operations.py` (mesmo router `/operations/companies/{company_id}`, mesmo estilo de rota fina sobre `OperationalService`):

- `GET /item-classifications` — fila paginada (`offset`, `limit`, filtro opcional `status`). Permissão `journal.read`, igual a `reviews`/`accounting_proposals`.
- `GET /item-classifications/{classification_id}` — detalhe com evidências e alternativas. Permissão `journal.read`.
- `POST /item-classifications/{classification_id}/decide` — corpo `{final_intent, decision_type, apply_scope}`. Permissão `accounting.classification.review`. Exige header `Idempotency-Key`, pelo mesmo motivo de `/reviews/{id}/approve|reject`: repetição de rede não pode gerar segunda decisão. `ReviewItemClassification` mantém `feedback_exists` como proteção de conteúdo (mesma chave, conteúdo diferente = conflito); a chave de idempotência do header protege contra repetição pura da mesma chamada.

Vocabulário de status que API e UI devem reconhecer, sem fallback genérico: nível item — `AUTO_CLASSIFIED`, `PRE_CLASSIFIED`, `REVIEW_REQUIRED`, `CONFLICTING_EVIDENCE`, `REVIEWED`; nível journey — `PENDING_RULE`, `ACCOUNT_MAPPING_REQUIRED`.

Motivo da separação de permissão: visualizar a fila é equivalente a visualizar qualquer revisão contábil já exposta (`journal.read`); decidir sobre uma classificação é o efeito com carga profissional, e por isso mantém a permissão dedicada criada na migration 0014.
