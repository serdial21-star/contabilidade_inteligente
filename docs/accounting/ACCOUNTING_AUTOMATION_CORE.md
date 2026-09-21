# Accounting Automation Core

O núcleo classifica `FiscalDocumentItem`, nunca apenas o documento. A sequência é item → evidências → intenção → confiança → mapping versionado → proposta → decisão humana. A automação pode preparar proposta, mas não aprova nem escritura.

O motor determinístico existente foi estendido; não existe motor paralelo. Catálogos antigos continuam no fluxo documental legado. Estado: domínio, schema e cenários sintéticos `READY`; orquestração persistente/API/UI ainda `PARTIAL`.

## Contrato da API de revisão por item (decidido em 2026-09-21, implementado em 2026-09-21)

A fila de revisão humana de `ItemClassification` segue o padrão já existente em `operations.py` (mesmo router `/operations/companies/{company_id}`, mesmo estilo de rota fina sobre `OperationalService`):

- `GET /item-classifications` — fila paginada (`offset`, `limit`), somente a versão mais recente de cada item e somente status `REVIEW_REQUIRED`/`CONFLICTING_EVIDENCE`. Permissão `journal.read`, igual a `reviews`/`accounting_proposals`.
- `GET /item-classifications/{classification_id}` — detalhe com evidências, alternativas e contexto do documento. Permissão `journal.read`.
- `POST /item-classifications/{classification_id}/decide` — corpo `{final_intent, decision_type, apply_scope}`. Permissão `accounting.classification.review`. **Correção da decisão original:** não exige `Idempotency-Key`. Ao implementar, `ReviewItemClassification` já é idempotente por conteúdo sem chave de cliente — `add_classification` reaproveita a linha quando o resultado é idêntico ao mais recente, e `feedback_exists` impede feedback/auditoria duplicados para o mesmo (classification, final_intent, apply_scope, actor). Exigir um header não verificado por ninguém seria pior do que não pedi-lo; adicionar verificação real exigiria coluna nova em `classification_feedback`, fora do escopo aditivo já fechado da migration 0014.

Vocabulário de status que API e UI devem reconhecer, sem fallback genérico: nível item — `AUTO_CLASSIFIED`, `PRE_CLASSIFIED`, `REVIEW_REQUIRED`, `CONFLICTING_EVIDENCE`, `REVIEWED`; nível journey — `PENDING_RULE`, `ACCOUNT_MAPPING_REQUIRED`.

Motivo da separação de permissão: visualizar a fila é equivalente a visualizar qualquer revisão contábil já exposta (`journal.read`); decidir sobre uma classificação é o efeito com carga profissional, e por isso mantém a permissão dedicada criada na migration 0014.

Implementação: rotas e `OperationalService` em `operations.py` (backend), fila/detalhe/decisão em `app.js` + `accounting-service.js` + `api-client.js` (frontend). UI ainda não cobre cadastro de `CompanyAccountingProfile`/CNAE — isso permanece fora desta fatia.
