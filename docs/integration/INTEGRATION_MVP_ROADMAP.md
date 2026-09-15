# Integration MVP Roadmap

Estimativas são relativas (`XS`, `S`, `M`, `L`, `XL`), não horas nem autorização de implementação.

## P0 Integration Readiness

| ID | Sistema | Issue | Por que importa | Antes de quê | Owner | Evidência necessária | Critério de aceitação |
| --- | --- | --- | --- | --- | --- | --- | --- |
| IR-P0-01 | A | Inventário runtime e versões conflitantes | Evita integrar endpoint legado/incorreto | freeze/Wave 1 | Owner Sistema A | export/lista n8n, tráfego e testes HOM | paths, métodos, schemas e owner aprovados; legados marcados |
| IR-P0-02 | A/B/Hub | Identidade M2M inexistente | Browser tokens são inadequados | qualquer chamada | Security/Platform | teste HMAC, rotação/revogação | credenciais separadas, scopes, replay e rate limit aprovados |
| IR-P0-03 | A | Permissões/guards fail-open e auditoria incerta | Pode expor portal/dados e enfraquecer efeito recebido | produção/piloto; A authorization antes do Hub | Owner A/Security | testes negativos e audit trail | APIs dedicadas fail-closed; auditoria persistente; portal hardening aprovado |
| IR-P0-04 | A/B | Namespace e schemas dedicados não congelados | Admin APIs têm lifecycle diferente | implementação Wave 1 | Arquitetura A+B | OpenAPI/event schemas versionados | `/api/integrations/v1/*` e compatibilidade aprovados |
| IR-P0-05 | B | `EXTERNAL_REFERENCE_GAP` | CNPJ sozinho não resolve duplicatas/correções | Wave 2 | Owner B/master data | desenho+testes de unicidade/ambiguidade | mapping tenant-aware, sem FK cruzada, revisão manual |
| IR-P0-06 | A/B | Transporte documental seguro não contratado | Drive/link mutável não garante evidência | Wave 3 | Owners Documents/Storage | URL curta e threat tests | pull escopado, hash/quarentena, expiry e evidência imutável |
| IR-P0-07 | A/B/Hub | Outbox/inbox, idempotência, retry e DLQ ausentes/não comprovados | At-least-once pode perder/duplicar efeito | Waves 2–5 | Platform + domain owners | testes timeout/duplicate/recovery | mesma chave/hash no-op; conflito detectado; DLQ reconciliável |
| IR-P0-08 | A | Kanban responde sucesso sem persistência confiável | Tarefa integrada pode desaparecer | Wave 4 | Owner A Operations | write/read e concorrência em HOM | tarefa persiste uma vez e retorna ref estável |
| IR-P0-09 | A | Upload/publicação admin→cliente ausente | Impede retorno de documentos ao portal | Wave 6 | Owner A Documents | E2E HOM | publicação idempotente, autorizada e auditada |
| IR-P0-10 | Todos | Homologações isoladas/E2E inexistentes | Produção não pode ser laboratório | qualquer pilot | Platform/QA | mapa ambiental + execução | A HOM↔Hub HOM↔B HOM, secrets/storage/logs separados |

## Ondas

| Onda | Objetivo | Entregas planejáveis | Estimativa | Dependências |
| --- | --- | --- | --- | --- |
| 0 | Estabilização e contract freeze | IR-P0-01, guards/audit A, owners, schemas e threat model | L | acesso/equipe do Sistema A |
| 1 | Fundação M2M/Hub | auth, assinatura, service principals, envelope, inbox/outbox, retry/DLQ, observabilidade HOM | XL | Wave 0; infra/secret store |
| 2 | Client sync | referências externas, CNPJ+mapping, create/update/disable e reconciliação | M | Waves 0–1; IR-P0-05 |
| 3 | Document intake | `DOCUMENT_RECEIVED`, URL curta/pull, hash/quarentena/evidência, NF-e/OFX receipt | XL | Waves 1–2; storage HOM |
| 4 | Exceptions/tasks | `FISCAL_EXCEPTION_CREATED`, `ACCOUNTING_REVIEW_REQUIRED`, `TASK_REQUIRED`, ack | L | Wave 3; Kanban corrigido |
| 5 | Decision visibility | approved/rejected callbacks minimizados, reconciliação | M | Wave 4; guardas de decisão B |
| 6 | Publication/obligations | documents back to portal, published ack, obligations/tax documents | XL | Wave 5; IR-P0-09; privacy/legal |

O MVP mínimo é Waves 1–5 após Wave 0. Wave 6 é posterior e não condiciona validar cliente→documento→processamento→tarefa→decisão.

## Fluxo de aceitação sintético

1. Sincronizar empresa sintética com CNPJ válido fictício e referência A; repetir e obter `no_op`.
2. Cliente sintético envia NF-e sintética no Portal A; A confirma metadado/arquivo e emite `DOCUMENT_RECEIVED`.
3. B baixa por URL curta, valida hash, cria evidência uma vez e processa NF-e.
4. Regra determinística versionada gera proposta ligada à revisão/hash.
5. `ACCOUNTING_REVIEW_REQUIRED` gera exatamente uma tarefa em A com resumo seguro.
6. Profissional autorizado aprova no B; nenhuma ação no A pode aprovar.
7. B emite `ACCOUNTING_PROPOSAL_APPROVED`; A registra visibilidade operacional.
8. Auditoria/correlação permitem navegar o percurso sem payload sensível. Repetir todos os eventos não duplica documento, NF-e, proposta ou tarefa.

## Matriz de falhas

| Falha | Owner da recuperação | Retry | DLQ/manual | Impacto visível |
| --- | --- | --- | --- | --- |
| CNPJ/ref desconhecido | Master data B + operação | não automático | revisão de correlação | item “empresa não correlacionada” |
| Evento duplicado | consumidor | não necessário | somente se hash conflitar | nenhum efeito duplicado |
| Documento indisponível/URL expirada | A Documents/Hub | renovar grant; limitado | após máximo | processamento aguardando fonte |
| XML inválido | B Documents/Fiscal | não | exceção/tarefa | documento rejeitado para processamento, original preservado |
| B indisponível | Hub/Platform B | exponencial | DLQ após 5 | A mostra pendente de integração |
| A indisponível | Hub/Platform A | exponencial | DLQ após 5 | decisão existe no B; visibilidade/tarefa atrasada |
| Timeout após efeito | consumidor/Hub | consultar por key antes de reenviar | reconciliação se desconhecido | estado “reconciliando”, não falso sucesso |
| Retries esgotados | owner do contrato | não cíclico | obrigatório + alerta | status seguro e ação operacional |
| Assinatura/replay inválido | Security | não | incidente se recorrente | resposta genérica, sem detalhes |

## Gates de saída

Homologação exige testes positivos/negativos de tenant/company, auth, replay, idempotência conflitante, concorrência, timeout/UNKNOWN, DLQ/replay, documento inválido, indisponibilidade bilateral e ausência de dados reais. Produção exige ainda Security 11, Observability 12, LGPD/Legal 13 e QA integrado 14.
