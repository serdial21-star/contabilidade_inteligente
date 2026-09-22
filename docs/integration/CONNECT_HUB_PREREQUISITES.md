# Connect Hub Prerequisites

## Matriz de pré-requisitos

| ID | Descrição | Status atual | Evidência | Bloqueia client sync? | Bloqueia document sync? | Bloqueia task callback? | Bloqueia produção? | Ação |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| CHP-01 | Repositório/tag do frontend A e route registry | `PARTIAL` (2026-09-22: frontend + n8n + MySQL agora todos inspecionados; ainda sem tag/commit por ser export, não clone git) | source completo do frontend, 60 workflows n8n e 30 tabelas MySQL; ver `SYSTEM_A_RUNTIME_VERIFICATION.md` "Atualização 2026-09-22" | Sim | Sim | Sim | Sim | obter tag/versão do export; route registry completo ainda não confirmado |
| CHP-02 | Inventário/export dos workflows ativos | `VERIFIED_IN_AVAILABLE_CODE` (2026-09-22) | 60 exports JSON reais, todos `active: true`, com path/método/auth de cada webhook | Sim | Sim | Sim | Sim | resolvido — falta apenas confirmar no runtime de homologação |
| CHP-03 | Freeze dos contratos atuais | `CONFIRMED_BLOCKER` (2026-09-22: conflitos agora confirmados por export real, não mais por dossiê) | 60 workflows exportados, TODOS `active:true` — versões antigas e novas coexistem de fato em produção, não é código morto | Sim | Sim | Sim | Sim | dono do Sistema A decide quais versões desativar; nenhuma versão nova deve ser criada |
| CHP-04 | Cliente master e CNPJ atuais | `VERIFIED_IN_AVAILABLE_CODE` para estrutura (2026-09-22) | schema real de `clientes` confirmado (`cnpj varchar(20)` com `UNIQUE KEY`, `senha` armazenada na própria tabela); dados reais não lidos | Sim | Sim | Sim | Sim | normalização/mapping ainda a implementar no B; estrutura já não é mais o bloqueador |
| CHP-05 | Referência externa no B | `CONFIRMED_BLOCKER` | gap verificado na Phase 09A | Sim | Sim | Sim | Sim | capacidade tenant-aware em futura fase autorizada |
| CHP-06 | Auth/autorização A fail-closed | `RESOLVED` (2026-09-22 parte 3: os 3 workflows de permissões foram corrigidos e importados em produção pelo dono do Sistema A — default passa a negar sem linha explícita) | ver SG-03/SYSTEM_A_SECURITY_GAPS.md "Atualização 2026-09-22 (parte 3)"; trigger de banco (cliente novo = tudo liberado) não foi alterado, é decisão de produto separada (SG-19/0b-9) | Sim | Sim | Sim | Sim | resolvido do lado do workflow; decisão sobre o trigger/fallback por cargo (SG-19) segue em aberto, não bloqueia |
| CHP-07 | Credencial/principal M2M | `MISSING` | nenhum mecanismo demonstrado | Sim | Sim | Sim | Sim | projetar/implementar somente após novo escopo |
| CHP-08 | Namespace API dedicado | `PARTIAL`, com contexto novo: n8n hospeda todos os 60 endpoints hoje, sem namespace `/api/integrations/v1` dedicado | n8n hospeda UI; nenhum contrato dedicado | Sim | Sim | Sim | Sim | confirmar hosting e congelar `/api/integrations/v1/*` |
| CHP-09 | Intake cliente e metadata documental | `VERIFIED_IN_AVAILABLE_CODE` (2026-09-22) | schema de `inbox_documentos` confirmado (FK para `tickets_master`/`entregas_master`, `cliente_id NOT NULL`) | Não | Sim | Não | Sim | mapping de campos para o contrato do B |
| CHP-10 | Transporte documental curto/escopado | `CONFIRMED_BLOCKER` | Drive usa link direto (`webViewLink`/`webContentLink`), sem URL curta/escopada nem expiração | Não | Sim | Não | Sim | definir grant/secure pull, hash, expiry e SSRF controls |
| CHP-11 | Central Ops list/create | `PARTIAL`, agora com código real lido | workflows de kanban/create existem e estão ativos; teste de execução real ainda não feito | Não | Não | Sim | Sim | teste create/read sintético HOM |
| CHP-12 | Central Ops update persiste | `RESOLVED_AND_VERIFIED` (2026-09-22 parte 3) | a checagem de `affectedRows` não funcionou nesta versão do node MySQL (só devolve `{success:true}`); corrigido com releitura do item após o update, testado em produção movendo cartões reais no Kanban | Não | Não | Sim | Sim | resolvido; teste de concorrência (duas atualizações simultâneas) ainda não realizado |
| CHP-13 | Idempotência/outbox/inbox/retry/DLQ | `CONFIRMED_BLOCKER` | capacidade não demonstrada em A/Hub | Sim | Sim | Sim | Sim | design+testes antes de Hub MVP |
| CHP-14 | Auditoria dos writes A | `PARTIAL_COVERAGE_CONFIRMED` (2026-09-22, antes `UNKNOWN`) | `logs_auditoria` existe e é escrita por 18/60 workflows; login, permissões, update de Kanban e upload de documento NÃO escrevem nela | Sim | Sim | Sim | Sim | ampliar cobertura de auditoria para as ações mais sensíveis antes de aceitar como evidência de efeito |
| CHP-15 | CORS/OPTIONS browser | `PARTIAL`, agora com evidência de código: todas as respostas usam `Access-Control-Allow-Origin: "*"` | confirmado em todos os workflows lidos; não exercitado por chamada real | Não para M2M | Não para M2M | Não para M2M | Sim portal | matriz de origins/headers por endpoint em HOM; considerar allowlist em vez de wildcard |
| CHP-16 | Homologação isolada A | `MISSING` | nenhum URL/DB/Drive/credential set fornecido | Sim | Sim | Sim | Sim | criar frontend+n8n+DB+Drive+secrets HOM |
| CHP-17 | Admin→cliente publication | `RESOLVED` (2026-09-22, antes `MISSING`) | workflow `admin/upload-documento-cliente` existe, está ativo e implementa o fluxo completo (Drive + 4 tabelas de destino conforme o módulo) | Não | Não cliente→B | Não | Wave 6 | nenhuma — item fechado do lado do Sistema A |
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

**Atualização 2026-09-21:** bloqueador #3 (autorização fail-closed/auditoria) sai de `NOT_VERIFIABLE` para `CONFIRMED_BLOCKER` — ver CHP-06 e `SYSTEM_A_SECURITY_GAPS.md` (SG-03). `BLOCKERS CONFIRMED` passa de 6 para 7. Os demais oito bloqueadores permanecem sem mudança de classificação; a evidência nova (relatório de varredura de terceiros, sem snapshot de repositório nem export do n8n) não satisfaz o "verification package" da seção seguinte — apenas fortalece a evidência já registrada. Nenhum código, banco, workflow, credencial ou deploy foi alterado.

**Atualização 2026-09-22:** itens 2 (workflows n8n) e 4 (schema MySQL) do "verification package" abaixo foram entregues e lidos (estrutura apenas; dados reais recebidos por engano foram descartados antes da leitura, ver `SYSTEM_A_SECURITY_GAPS.md`). Bloqueador #3 permanece `CONFIRMED_BLOCKER`, agora com evidência de backend (não só frontend). Bloqueador #8 (Kanban update) sai de `NOT_VERIFIABLE` para `CONFIRMED_BLOCKER` com causa raiz identificada — deixa de ser "sem evidência" e passa a "problema específico e corrigível". CHP-17 (upload admin→cliente) é dado como `RESOLVED`. `BLOCKERS CONFIRMED` passa de 7 para 8 (bloqueador #8 antes contava como `NOT_VERIFIABLE`, agora conta como confirmado); `BLOCKERS RESOLVED: 1` (CHP-17, fora da contagem dos nove porque não estava na lista original de nove). Itens 1 (homologação), 3 (fixtures Drive), 6 (matriz de credenciais) e 7 (test runner) do pacote seguinte continuam pendentes — por isso o gate segue fechado.

## Verification package necessário

1. URL/identificação de homologação e owner técnico. — **pendente**
2. Source snapshot/tag do frontend A, lockfile e configurações com valores redigidos. — **entregue 2026-09-21** (sem tag de commit, é export)
3. Exports JSON redigidos dos workflows relevantes, incluindo status ativo, método, path e response mode. — **entregue 2026-09-22** (60 workflows, todos `active: true`)
4. Schema-only/read-only do MySQL e constraints/indexes, sem linhas de clientes. — **entregue 2026-09-22** (30 tabelas; chegou com dados reais por engano, descartados antes da leitura — repita a exportação em phpMyAdmin desmarcando "Dados" da próxima vez)
5. Descrição/fixtures sintéticas de Drive, pastas e URLs. — **pendente**
6. Matriz de credenciais por ambiente sem valores secretos. — **pendente**
7. Runner ou coleção de testes contra HOM para auth, permissions, CRUD, CORS e erros. — **pendente**

Com os itens 1, 5, 6 e 7, a Phase 09B pode ser encerrada com teste real, sem tocar produção.
