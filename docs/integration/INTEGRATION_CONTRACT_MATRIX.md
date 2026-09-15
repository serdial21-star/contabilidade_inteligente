# Integration Contract Matrix

Namespace canônico reservado: `/api/integrations/v1/*`. Todos os itens abaixo têm status `PROPOSED_CONTRACT`; nenhum endpoint, evento ou credencial foi implementado.

| ID | Direção | Produtor | Consumidor | Método / evento | Versão | Auth | Idempotência | Entrada | Saída | Owner | Escopo | Status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| IC-001 | A→B | Sistema A | Sistema B | `POST /api/integrations/v1/companies/sync` / `CLIENT_CREATED` | v1 | HMAC M2M | event/key + payload hash | ref externa, CNPJ, razão/nome, estado ativo, contacts opcionais | company correlation, result | B | MVP-1 | `PROPOSED_CONTRACT` |
| IC-002 | A→B | Sistema A | Sistema B | mesmo endpoint / `CLIENT_UPDATED` | v1 | HMAC M2M | event/key + hash | campos alterados, versão/fonte | correlation, applied/no-op/conflict | B | MVP-1 | `PROPOSED_CONTRACT` |
| IC-003 | A→B | Sistema A | Sistema B | mesmo endpoint / `CLIENT_DISABLED` | v1 | HMAC M2M | event/key + hash | ref, CNPJ, disabled_at, reason_code | no-op/disabled/review | B | MVP-1 | `PROPOSED_CONTRACT` |
| IC-004 | A→B | Sistema A | Sistema B | `POST /api/integrations/v1/documents/intake` / `DOCUMENT_RECEIVED` | v1 | HMAC M2M | external document ref + hash | company ref, file metadata, category, competence, URL curta | receipt/document ref/status | B | MVP-2 | `PROPOSED_CONTRACT` |
| IC-005 | B→A | Sistema B | Sistema A | `POST /api/integrations/v1/accounting-events` / processing events | v1 | HMAC M2M | event ID | refs, safe status/error code | receipt | A | MVP-3 | `PROPOSED_CONTRACT` |
| IC-006 | B→A | Sistema B | Sistema A | `POST /api/integrations/v1/tasks` / `TASK_REQUIRED` | v1 | HMAC M2M | event + exception/proposal ref | company, category, priority, safe summary, deep link | A task ref/status | A | MVP-4 | `PROPOSED_CONTRACT` |
| IC-007 | A→B | Sistema A | Sistema B | `POST /api/integrations/v1/tasks/acknowledgements` | v1 | HMAC M2M | task external ref + transition ID | refs, operational status, occurred_at | receipt | B | MVP-4 | `PROPOSED_CONTRACT` |
| IC-008 | B→A | Sistema B | Sistema A | `POST /api/integrations/v1/decisions/status` / approved/rejected | v1 | HMAC M2M | decision event ID | proposal ref, safe decision status, occurred_at | receipt | A | MVP-5 | `PROPOSED_CONTRACT` |
| IC-009 | A→B | Sistema A | Sistema B | `POST /api/integrations/v1/documents/access-grants` | v1 | HMAC M2M | document ref + grant nonce | short-lived scoped download reference | accepted/expired | A | MVP-2 | `PROPOSED_CONTRACT` |
| IC-010 | B→A | Sistema B | Sistema A | `POST /api/integrations/v1/publications` / `DOCUMENT_AVAILABLE` | v1 | HMAC M2M | artifact/event ID | company, artifact ref, safe metadata | queued/rejected | A | LATER | `PROPOSED_CONTRACT` |
| IC-011 | A→B | Sistema A | Sistema B | `DOCUMENT_PUBLISHED` callback | v1 | HMAC M2M | publication event ID | publication ref/status/timestamp | receipt | B | LATER | `PROPOSED_CONTRACT` |
| IC-012 | A→B | Sistema A | Sistema B | `OBLIGATION_CREATED` / `TAX_DOCUMENT_AVAILABLE` | v1 | HMAC M2M | event ID | minimized operational refs | receipt | domínio receptor | LATER | `PROPOSED_CONTRACT` |

## Contrato de cliente

Campos obrigatórios: `external_reference {system,type,id}`, `business_key {type:"CNPJ",value:<14 digits>}`, `display_name`, `active`, `source_updated_at`, `idempotency_key`. Opcionais: razão social, nome fantasia, contatos minimizados e Drive relationship opaco quando necessário. `cliente_id` não vira PK no B. Resposta distingue `created`, `updated`, `no_op`, `conflict` e `manual_review_required`. CNPJ ausente/inválido ou correlação ambígua retorna 422 estável e não cria vínculo automático.

## Compatibilidade e erros

Mudança aditiva compatível permanece v1; remoção, nova semântica ou campo obrigatório exige v2. Receptores rejeitam versão desconhecida. Códigos mínimos: `INVALID_SIGNATURE`, `REPLAY_DETECTED`, `VALIDATION_FAILED`, `UNKNOWN_COMPANY`, `AMBIGUOUS_CORRELATION`, `IDEMPOTENCY_CONFLICT`, `DOCUMENT_UNAVAILABLE`, `RATE_LIMITED`, `TEMPORARY_UNAVAILABLE`. 4xx determinístico não sofre retry; 429/5xx/timeout seguem política transitória.

## Ownership de idempotência

O produtor cria e preserva IDs/chaves; Hub mantém entrega/DLQ sem regenerá-los; consumidor mantém inbox/resultado e compara hash. O domínio documental também protege duplicidade por referência externa e hash; processadores NF-e/OFX e geração de proposta reutilizam suas próprias chaves derivadas, impedindo efeito duplicado em cascata.
