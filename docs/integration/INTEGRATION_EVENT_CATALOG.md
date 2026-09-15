# Integration Event Catalog

Todos são contratos propostos v1, entregues *at least once*. Payload comum usa o envelope de `CONNECT_HUB_ARCHITECTURE.md`; campos abaixo são o `payload`. Dados brutos, tokens e credenciais são proibidos.

| Evento | Produtor → consumidor | Gatilho | Payload mínimo | Classe | Idempotência / retry | Sensibilidade | MVP |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `CLIENT_CREATED` | A→B | cliente operacional confirmado | external ref, CNPJ, display name, active, source version | fato | event ID + client ref; transitório | identificação empresarial/contacts opcionais | MVP-1 |
| `CLIENT_UPDATED` | A→B | alteração relevante confirmada | refs, changed fields, source version/time | fato | event ID; ordering/version guard | empresarial | MVP-1 |
| `CLIENT_DISABLED` | A→B | soft-disable confirmado | refs, disabled_at, reason_code | fato | event ID; nunca delete | empresarial | MVP-1 |
| `DOCUMENT_RECEIVED` | A→B | metadado+arquivo confirmados no A | document ref, company ref, filename, category, competence, media type, size/hash quando disponível | fato | document ref + hash; transitório | nome/metadados | MVP-2 |
| `DOCUMENT_AVAILABLE` | B→A | artefato aprovado pronto para fluxo operacional | artifact ref, company ref, category, competence | fato/comando subsequente | artifact/event ID | metadados | LATER |
| `DOCUMENT_PROCESSING_FAILED` | B→A | falha final ou intervenção requerida | refs, safe error code, retryable, occurred_at | fato | processing attempt/event ID | resumo seguro | MVP-3 |
| `FISCAL_DOCUMENT_PROCESSED` | B→A | NF-e processada com segurança | refs, type/model, competence, status, counts | fato | fiscal document/event ID | fiscal minimizado | MVP-3 |
| `FISCAL_EXCEPTION_CREATED` | B→A | exceção fiscal persistida | exception ref, company ref, category, priority, safe summary | fato | exception/event ID | sensível; minimizar | MVP-4 |
| `ACCOUNTING_PROPOSAL_CREATED` | B→A | proposta persistida | proposal ref, company ref, status, competence | fato | proposal/event ID | contábil minimizado | LATER (telemetria) |
| `ACCOUNTING_REVIEW_REQUIRED` | B→A | proposta requer decisão humana | proposal ref, company ref, priority, safe summary/deep link | fato | review/event ID | contábil minimizado | MVP-4 |
| `ACCOUNTING_PROPOSAL_APPROVED` | B→A | aprovação válida/hash exato persistida | proposal ref, safe status, revision/hash ref, occurred_at | fato | decision/event ID | sem débitos/créditos no A | MVP-5 |
| `ACCOUNTING_PROPOSAL_REJECTED` | B→A | rejeição válida persistida | proposal ref, safe status, reason code opcional, occurred_at | fato | decision/event ID | motivo minimizado | MVP-5 |
| `TASK_REQUIRED` | B→A | exceção/revisão demanda ação operacional | source ref, company, category, priority, safe summary, deep link | solicitação | source ref + event ID | sem payload completo | MVP-4 |
| `DOCUMENT_PUBLISHED` | A→B | A publicou ao cliente | publication/artifact refs, channel, timestamp, status | fato | publication/event ID | metadados | LATER |
| `OBLIGATION_CREATED` | A→B | obrigação operacional confirmada | obligation ref, company, type, due date, status | fato | obligation/event ID | operacional/fiscal | LATER |
| `TAX_DOCUMENT_AVAILABLE` | A→B | guia fiscal disponível | document ref, company, competence, type, due date | fato | document/event ID | fiscal | LATER |

`CLIENT_DISABLED`, solicitado no contrato de sincronização, complementa o catálogo mínimo. Nenhum evento é `NOT_REQUIRED` permanentemente; `ACCOUNTING_PROPOSAL_CREATED` não integra o MVP porque review/decisão já atendem a necessidade operacional. Obrigações, guias e publicação são posteriores ao fluxo validado.

## Envelope v1

```json
{
  "event_id": "opaque-uuid",
  "event_type": "DOCUMENT_RECEIVED",
  "event_version": 1,
  "occurred_at": "2026-09-15T18:00:00Z",
  "source_system": "SERDIAL21_OPERATIONAL",
  "correlation_id": "opaque-id",
  "idempotency_key": "SERDIAL21_OPERATIONAL:DOCUMENT:opaque-id:v1",
  "company_external_reference": {
    "system": "SERDIAL21_OPERATIONAL",
    "type": "CLIENT",
    "id": "opaque-id"
  },
  "payload": {}
}
```

Eventos são imutáveis. Correções publicam novo evento causalmente relacionado; não reescrevem histórico. Ordenação global não é presumida: eventos de cliente carregam versão da fonte e consumidores rejeitam regressão. O retry padrão é no máximo cinco tentativas exponenciais com jitter para timeout/429/5xx, seguido de DLQ e reconciliação.
