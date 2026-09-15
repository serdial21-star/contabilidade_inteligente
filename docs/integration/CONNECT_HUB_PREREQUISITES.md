# Connect Hub Prerequisites

## Matriz de pré-requisitos

| ID | Descrição | Status atual | Evidência | Bloqueia client sync? | Bloqueia document sync? | Bloqueia task callback? | Bloqueia produção? | Ação |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| CHP-01 | Repositório/tag do frontend A e route registry | `NOT_VERIFIABLE` | source A ausente | Sim | Sim | Sim | Sim | fornecer snapshot/tag e manifest sem segredos |
| CHP-02 | Inventário/export dos workflows ativos | `NOT_VERIFIABLE` | apenas UI n8n pública responde | Sim | Sim | Sim | Sim | export redacted + IDs/status/responseMode |
| CHP-03 | Freeze dos contratos atuais | `CONFIRMED_BLOCKER` | sete conflitos restantes | Sim | Sim | Sim | Sim | resolver por source+export+HOM; não criar versão nova |
| CHP-04 | Cliente master e CNPJ atuais | `PARTIAL` | dossiê cita `clientes`; schema ausente | Sim | Sim | Sim | Sim | schema read-only + fixtures sintéticas + normalização adapter |
| CHP-05 | Referência externa no B | `CONFIRMED_BLOCKER` | gap verificado na Phase 09A | Sim | Sim | Sim | Sim | capacidade tenant-aware em futura fase autorizada |
| CHP-06 | Auth/autorização A fail-closed | `NOT_VERIFIABLE` | código e testes A ausentes | Sim | Sim | Sim | Sim | testes 401/403, empty permissions e unknown module |
| CHP-07 | Credencial/principal M2M | `MISSING` | nenhum mecanismo demonstrado | Sim | Sim | Sim | Sim | projetar/implementar somente após novo escopo |
| CHP-08 | Namespace API dedicado | `PARTIAL` | n8n hospeda UI; nenhum contrato dedicado | Sim | Sim | Sim | Sim | confirmar hosting e congelar `/api/integrations/v1/*` |
| CHP-09 | Intake cliente e metadata documental | `PARTIAL` | endpoints/tabela apenas documentados | Não | Sim | Não | Sim | validar upload sintético, Drive e `inbox_documentos` |
| CHP-10 | Transporte documental curto/escopado | `CONFIRMED_BLOCKER` | nenhuma evidência atual | Não | Sim | Não | Sim | definir grant/secure pull, hash, expiry e SSRF controls |
| CHP-11 | Central Ops list/create | `PARTIAL` | contratos divergentes/não testados | Não | Não | Sim | Sim | teste create/read sintético HOM |
| CHP-12 | Central Ops update persiste | `CONFIRMED_BLOCKER` | relato histórico; nenhuma evidência de correção | Não | Não | Sim | Sim | teste update/read e concorrência |
| CHP-13 | Idempotência/outbox/inbox/retry/DLQ | `CONFIRMED_BLOCKER` | capacidade não demonstrada em A/Hub | Sim | Sim | Sim | Sim | design+testes antes de Hub MVP |
| CHP-14 | Auditoria dos writes A | `UNKNOWN` | `logs_auditoria` não verificada | Sim | Sim | Sim | Sim | demonstrar eventos mínimos e atomicidade possível |
| CHP-15 | CORS/OPTIONS browser | `NOT_VERIFIABLE` | webhooks não exercitados | Não para M2M | Não para M2M | Não para M2M | Sim portal | matriz de origins/headers por endpoint em HOM |
| CHP-16 | Homologação isolada A | `MISSING` | nenhum URL/DB/Drive/credential set fornecido | Sim | Sim | Sim | Sim | criar frontend+n8n+DB+Drive+secrets HOM |
| CHP-17 | Admin→cliente publication | `MISSING` documental | dossiês dizem webhook ausente | Não | Não cliente→B | Não | Wave 6 | confirmar runtime; implementar só no escopo futuro |
| CHP-18 | Privacidade/retention/legal hold cross-system | `FUTURE_DESIGN_REQUIRED` | Phase 09A | Não sintético | Não sintético | Não sintético | Sim real data | concluir Phase 13 antes de real data |

## Reavaliação dos nove bloqueadores MVP da Phase 09A

| # | Bloqueador original | Classificação 09B | Razão |
| --- | --- | --- | --- |
| 1 | Runtime inventory/contract freeze | `CONFIRMED_BLOCKER` | source/exports ausentes; sete conflitos persistem |
| 2 | Identidade M2M | `CONFIRMED_BLOCKER` | suporte não demonstrado |
| 3 | Autorização fail-closed/auditoria | `NOT_VERIFIABLE` | não há código/runtime autenticado |
| 4 | API dedicada/versionada | `PARTIAL` | hosting n8n plausível, contrato ausente |
| 5 | External reference | `CONFIRMED_BLOCKER` | gap do B permanece; A master não verificado |
| 6 | Transporte documental seguro | `CONFIRMED_BLOCKER` | nenhuma URL curta/controle comprovado |
| 7 | Entrega durável/idempotência/DLQ | `CONFIRMED_BLOCKER` | não demonstrado |
| 8 | Kanban update/persistência | `NOT_VERIFIABLE` e bloqueia gate | não foi possível confirmar correção |
| 9 | Homologação/E2E | `CONFIRMED_BLOCKER` | ambiente não apresentado |

`BLOCKERS RESOLVED/STALE: 0`. `BLOCKERS CONFIRMED: 6`; três permanecem `PARTIAL/NOT_VERIFIABLE`, portanto continuam fechando o gate por ausência de evidência.

## Verification package necessário

1. URL/identificação de homologação e owner técnico.
2. Source snapshot/tag do frontend A, lockfile e configurações com valores redigidos.
3. Exports JSON redigidos dos workflows relevantes, incluindo status ativo, método, path e response mode.
4. Schema-only/read-only do MySQL e constraints/indexes, sem linhas de clientes.
5. Descrição/fixtures sintéticas de Drive, pastas e URLs.
6. Matriz de credenciais por ambiente sem valores secretos.
7. Runner ou coleção de testes contra HOM para auth, permissions, CRUD, CORS e erros.

Com esse pacote, a Phase 09B pode ser retomada sem tocar produção.
