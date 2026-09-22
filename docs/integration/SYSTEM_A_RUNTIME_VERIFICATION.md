# System A Runtime Verification

Data: 2026-09-15. Escopo: Phase 09B. Esta verificação não acessou dados de clientes, não autenticou no Sistema A, não chamou webhooks funcionais e não alterou produção.

## Conclusão executiva

`SYSTEM A RUNTIME EVIDENCE: BLOCKED`.

O workspace contém o código do **Sistema B**, os três dossiês e os artefatos da Phase 09A. Não contém o repositório React/Vite do Sistema A, exports JSON dos workflows n8n, schema/dump sanitizado do MySQL, configuração Supabase, configuração Drive ou evidência de homologação. Assim, não é possível confirmar rotas, guards, payloads, tabelas, persistência Kanban, CORS, auditoria ou sessões sem inventar evidência.

A única evidência runtime atual obtida com segurança é pública e read-only: `https://n8n.serdial21.com/` respondeu HTTPS `200` em 2026-09-15, servido por Caddy, e o HTML identifica n8n release `2.6.4`. Isso confirma apenas que a interface n8n responde; não confirma workflows ativos, endpoints `/webhook/*`, banco, credenciais ou ambiente de homologação.

Nenhum P0 foi corrigido: não há código do Sistema A disponível e uma alteração no Sistema B seria fora de escopo.

## Pre-flight

- branch: `main`;
- HEAD: `4ece8d1 docs: complete phase 09A integration readiness architecture`;
- worktree já estava sujo com mudanças da Phase 09 em frontend/backend/testes: todas classificadas `PRE_EXISTING_CHANGE` e preservadas;
- inputs presentes em `docs/integration-input/`: 3/3;
- nenhum `package.json`, `vite.config.*`, `.tsx`, export n8n ou schema SQL do Sistema A foi encontrado no workspace.

## Classificação das afirmações dos dossiês

| Afirmação | Classificação 09B | Evidência atual |
| --- | --- | --- |
| Serviço n8n em `n8n.serdial21.com` | `VERIFIED_CURRENT` somente para a UI raiz | HTTPS 200; HTML n8n 2.6.4; Caddy |
| Base funcional `/webhook/*` e workflows listados | `RUNTIME_VERIFICATION_REQUIRED` | não foram fornecidos exports/acesso autorizado; webhooks não foram invocados |
| React/Vite/Vercel e route registry descrito | `NOT_VERIFIABLE_FROM_REPOSITORY` | código A ausente |
| Supabase Edge Functions como proxy do portal | `NOT_VERIFIABLE_FROM_REPOSITORY` | código/config A ausentes |
| MySQL Hostinger e tabelas descritas | `RUNTIME_VERIFICATION_REQUIRED` | sem acesso read-only/schema sanitizado |
| Google Drive para documentos | `RUNTIME_VERIFICATION_REQUIRED` | sem código/workflow/config; não foram abertos links de clientes |
| SMTP Hostinger e WhatsApp Z-API | `RUNTIME_VERIFICATION_REQUIRED` | sem config/logs; nenhum envio realizado |
| Endpoints “OK aparente” | `NOT_VERIFIABLE_FROM_REPOSITORY` | são afirmações do dossiê, não testes 09B |
| Rotas `/cliente/*` | `STALE` provável | dossiê mais novo documenta `/portal/*`; runtime ainda requerido |
| Dashboard/agenda/create/update/impostos/equipe | `CONFLICTING` | versões/namespaces divergem entre os três inputs |
| Upload `/admin/upload-documento-cliente` ausente | `RUNTIME_VERIFICATION_REQUIRED` | `MISSING` nos dossiês; não confirmado no n8n atual |
| Update Kanban retorna sucesso sem persistir | `RUNTIME_VERIFICATION_REQUIRED` | relato histórico sem teste atual |

## Arquitetura e configurações atuais

| Componente | Resultado | Path/config canônico verificável |
| --- | --- | --- |
| Frontend framework/version | não verificável | nenhum source/manifest A disponível |
| Vite/build | não verificável | nenhum `vite.config`/`package.json` A |
| n8n | parcial | host público verificado; release 2.6.4 exposta no HTML; workflows desconhecidos |
| Supabase Edge Functions | não verificável | nomes históricos apenas |
| MySQL | não verificável | `DB_RUNTIME_VERIFICATION: NOT_AVAILABLE` |
| Google Drive | não verificável | campos/pastas conflitantes |
| SMTP | não verificável | nenhum teste/env/log |
| WhatsApp | não verificável | fornecedor Z-API documentado, estado runtime desconhecido |

Não foram lidos nem registrados segredos. A versão exposta pelo HTML é metadado público; sua adequação/patch level deve ser avaliada pelo owner de infraestrutura sem upgrade nesta fase.

## Rotas e autorização

As rotas de cliente documentadas são `/dashboard`, `/biblioteca`, `/chamados`, `/documentos`, `/impostos` e `/honorarios`; as administrativas incluem `/admin`, `/admin/clientes`, `/admin/documentos`, `/admin/tickets`, `/admin/equipe`, `/admin/impostos`, `/admin/honorarios` e `/admin/configuracoes`. Como o registry e os componentes de guard não estão disponíveis:

- `CLIENT ROUTE GUARDS: PARTIAL` — há alegação de ausência nos dossiês, não verificação atual;
- `PERMISSIONS FAIL CLOSED: FAIL` como gate de prontidão — não há evidência positiva atual de fail-closed;
- testes autorizado/não autorizado/permissão vazia/módulo desconhecido: `NOT_RUN`, pois o código/runtime autenticado não foi fornecido;
- admin guards e permission checks: `RUNTIME_VERIFICATION_REQUIRED`.

“FAIL” no gate não afirma exploração atual; significa que o requisito obrigatório não tem evidência suficiente para ser aprovado.

## Autenticação, sessão e tokens

Os dossiês documentam login cliente `/portal-serdial-v2`, login admin `/admin/login-v2`, bearer tokens em `localStorage` (`auth_token`/`admin_auth_token`) e logout local. Não foi possível verificar emissão, hash, expiry, lookup, 401, revogação ou tabelas.

- `SESSION MODEL: PARTIAL`;
- `security_sessoes_funcionarios` é a indicação mais detalhada/recente do dossiê técnico, mas `admin_sessoes` também foi citado: fonte canônica **não resolvida**;
- `LOGOUT REVOCATION: GAP` até haver evidência de revogação server-side;
- browser tokens são proibidos para M2M.

## Clientes, CNPJ e Drive

- `CLIENT MASTER CONTRACT: PARTIAL`: `clientes` e `cliente_id` são documentados, não verificados;
- `CNPJ CORRELATION: PARTIAL`: saída futura pode normalizar para 14 dígitos sem mutar armazenamento A, mas formato/constraints atuais são desconhecidos;
- `DRIVE FOLDER FIELD: UNRESOLVED`: `drive_folder_id` versus `id_pasta_raiz`;
- a correlação técnica permanece referência externa + CNPJ normalizado, nunca PK/FK cruzada.

## Documentos

O fluxo browser → proxy Supabase (portal) ou fetch admin → n8n → Drive + MySQL é apenas documentado. `inbox_documentos`, seus campos e atomicidade não foram verificados.

- `DOCUMENT RECEIPT: PARTIAL`;
- `ADMIN CLIENT PUBLICATION: MISSING` conforme evidência documental, ainda requer confirmação runtime; é `DEFERRED` para o MVP cliente→B;
- `SECURE DOCUMENT TRANSPORT: BLOCKER`: não há evidência de URL curta/escopada; URLs públicas/permanentes também não foram confirmadas;
- nenhum arquivo, link Drive ou dado real foi acessado.

## Central de Operações

| Operação | Contrato documentado | Resultado 09B |
| --- | --- | --- |
| List | `/admin-kanban-v3` | `PARTIAL` — não testado |
| Create | `/admin-create-item-v3` ou `v5` | `PARTIAL` — conflito e não testado |
| Update | `/admin-update-item-v1` ou `v5` | `FAIL` no gate — persistência não comprovada e versões conflitantes |
| Delete | `/admin-delete-item-v3` | `PARTIAL` — sem confirmação de delete/soft-delete |

`KANBAN STATUS PERSISTENCE: FAIL` no gate, pois o teste create→read→update→read→delete não pôde ser executado. O contrato de campos (`id`, `id_origem`, `tipo_item`, `titulo`, cliente, status bruto/padronizado, responsável, departamento, prioridade e datas) permanece documental.

Status de tasks, tickets, obligations e deliveries não devem ser unificados. O mapping seguro só pode ser congelado depois de fixtures sintéticas mostrarem os valores reais de cada origem.

## Banco, auditoria, CORS e erros

- `MYSQL SCHEMA VERIFIED: NO`;
- tabelas `clientes`, `funcionarios`, `inbox_documentos`, `tasks_master`/`tarefas_internas`, `tickets_master`, `entregas_master`, `impostos_obrigacoes`, permissões, sessões e `logs_auditoria`: `NOT_VERIFIABLE`;
- `AUDIT: UNKNOWN`;
- `CORS_BROWSER_READINESS: PARTIAL` — não foram exercitados webhooks; M2M não depende de CORS;
- padrão `success/message/data`: documental; variantes reais desconhecidas;
- rejeição 401 para token ausente/inválido/expirado: não testada;
- `DATABASE SCHEMA CHANGED: NO`.

## n8n e capacidade de integração

- `N8N RUNTIME INSPECTED: PARTIAL`: somente UI pública/versão; workflows, status, `Respond to Webhook`, `lastNode` e SQL não inspecionados;
- `M2M_CREDENTIAL SUPPORT: MISSING` pela evidência disponível; nenhum mecanismo de serviço foi demonstrado;
- `INTEGRATION_API_HOSTING: PARTIAL`: n8n pode tecnicamente hospedar webhooks, mas namespace, auth, autorização, idempotência e observabilidade dedicados não existem como evidência;
- `SYSTEM A HOMOLOGATION: MISSING`: nenhum frontend/n8n/DB/Drive/credential set separado foi apresentado.

## Correções

`P0 FIXES IMPLEMENTED: 0`. Nenhum problema satisfaz simultaneamente evidência atual, código disponível, mudança localizada, teste e rollback. Criar correção neste repositório alteraria o sistema errado.

## Decisão

O Sistema A não está demonstrado como pronto para implementação do Connect Hub. A próxima tarefa isolada deve ser adquirir um **verification package** do Sistema A: snapshot/tag do frontend, exports redacted dos workflows ativos, schema read-only sanitizado, manifest ambiental sem segredos e uma homologação sintética. Depois, repetir 09B e executar testes de contrato/persistência.

**PHASE 09B — SYSTEM A RUNTIME VERIFICATION: BLOCKED**

**SYSTEM A: NOT_READY_FOR_CONNECT_HUB_MVP**

**INTEGRATION: NO_GO**

## Atualização 2026-09-21 — evidência de terceiros (relatório de varredura Lovable)

Fonte: `docs/integration-input/RELATORIO_VARREDURA_LOVABLE_20260921.md`. Esta é a primeira evidência de nível código-fonte do Sistema A recebida neste workspace (frontend React + três Supabase Edge Functions), fornecida pelo dono do produto. Não é um snapshot/tag do repositório A nem cobre n8n/MySQL, portanto não satisfaz sozinha o "verification package" descrito em `CONNECT_HUB_PREREQUISITES.md`. A conclusão `BLOCKED`/`NO_GO` acima permanece válida e não foi reaberta; o que muda é a classificação de algumas linhas abaixo, de ausência de evidência para evidência positiva.

| Afirmação (09B original) | Classificação anterior | Classificação 2026-09-21 | Evidência |
| --- | --- | --- | --- |
| Permissions fail-closed / route guards | `NOT_VERIFIABLE_FROM_REPOSITORY`, "FAIL no gate" | `CONFIRMED_FAIL_OPEN_BY_SOURCE_REVIEW` — continua reprovando o gate, agora por defeito demonstrado, não por ausência de prova | Relatório itens 1, 11 (`usePermissoes.ts`, `useClientPermissoes.ts`, `useCanAccess.ts`, `App.tsx:78-79`, `ClientRouteGuard.tsx:16,51-54` apenas visual) |
| Supabase Edge Functions | `NOT_VERIFIABLE_FROM_REPOSITORY` | `CONFIRMED_UNAUTHENTICATED_BY_SOURCE_REVIEW` para `ai-analyst`/`proxy-file-upload`; demais funções não cobertas pelo relatório permanecem `NOT_VERIFIABLE` | Relatório item 4 (`supabase/config.toml:4-7`, `proxy-file-upload/index.ts:18-28`) |
| Padrão `success/message/data` | "documental; variantes reais desconhecidas" | `CONFIRMED_INCONSISTENT_BY_SOURCE_REVIEW` — existe em alguns call sites e é ignorado em outros | Relatório itens 3, 7 (`AdminAuthContext.tsx:53,112`; `useAdminDashboard.ts:58`; `useClientes.ts:24-25`; contraste com `useTickets.ts:25-33`, `useListas.ts:52-58`, `useAtalhos.ts:80`, que seguem o padrão correto) |
| Upload `/admin/upload-documento-cliente` ausente | `RUNTIME_VERIFICATION_REQUIRED` | ainda `RUNTIME_VERIFICATION_REQUIRED` para o backend n8n; confirmado como referenciado sem workflow correspondente do lado do frontend | Relatório item 9 (`AdminUploadDocumentosForm.tsx:183`) — evidência de chamada, não de ausência no n8n (que já era a afirmação do dossiê) |
| Update Kanban retorna sucesso sem persistir | `RUNTIME_VERIFICATION_REQUIRED` | inalterado — `RUNTIME_VERIFICATION_REQUIRED`; o relatório confirma apenas que o frontend chama `admin-update-item-v5` (`useTasks.ts:94-97`), não que o workflow persiste | Relatório item 9. Chamada de frontend não é efeito confirmado; `CHP-12` continua `CONFIRMED_BLOCKER`. |
| Sessão/tokens em `localStorage`, sem expiry/renovação | `PARTIAL` | `CONFIRMED_BY_SOURCE_REVIEW` | Relatório item 11 (`AdminAuthContext.tsx:59`, `apiClient.ts:9-11`) |

Achado novo sem equivalente nas afirmações 09B originais: uso de `webhook/admin/tickets` sem token em código legado ainda executável (`useTickets.ts`, relatório item 5) e registro de corpo/resposta completos em console (relatório item 10, `AdminAuthContext.tsx:99,103,114` e outros). Ambos são tratados em `SYSTEM_A_SECURITY_GAPS.md` (novo `SG-06`) e não alteram esta conclusão de fase.

Nenhum P0 foi corrigido nesta atualização; nenhum código, banco, workflow, credencial ou deploy foi alterado. A tarefa isolada recomendada (verification package completo) continua sendo o próximo passo antes de repetir a Phase 09B por inteiro.

## Atualização 2026-09-21 (parte 2) — código-fonte real do Sistema A disponibilizado

O dono do produto disponibilizou uma cópia local do frontend do Sistema A em `C:\Projetos\Sistema escritório\serdialconnect-hub-main` (fora deste repositório; não copiado nem versionado aqui). É um export do Lovable, não um clone git — não há `.git`, portanto não existe hash/tag de commit a registrar como evidência, apenas a data de exportação dos arquivos. `.env` está presente na pasta e **não foi lido**; nenhum segredo foi acessado, copiado ou registrado. Nenhum arquivo do Sistema A foi alterado; nenhum build, dev server, teste ou chamada de rede foi executado contra n8n/Supabase/MySQL reais.

Isso satisfaz o item 2 do "verification package" (`CONNECT_HUB_PREREQUISITES.md`: "source snapshot... do frontend A") de forma **parcial mas substancialmente mais forte** que o relatório de terceiros da atualização anterior: é o código-fonte real, não um resumo. Ainda faltam os itens 1, 3, 4, 5, 6, 7 (URL de homologação, export dos workflows n8n, schema MySQL real/read-only, fixtures de Drive, matriz de credenciais e um test runner contra HOM) — o n8n e o MySQL continuam fora deste material.

### Reclassificações para `VERIFIED_IN_AVAILABLE_CODE`

| Item | Classificação anterior | Nova classificação | Evidência (arquivo:linha real) |
| --- | --- | --- | --- |
| Fail-open em `pode()`/`podeAcessarCliente()` | `CONFIRMED_FAIL_OPEN_BY_SOURCE_REVIEW` (relatório de terceiros) | `VERIFIED_IN_AVAILABLE_CODE` | `src/hooks/usePermissoes.ts:98-104` (comentário do próprio código: `// If no permissions configured at all, allow everything (permissive fallback)`) |
| Fail-open em `useClientPermissoes` | idem | `VERIFIED_IN_AVAILABLE_CODE` | `src/hooks/useClientPermissoes.ts:85-88`, mesmo padrão, mesmo comentário de fallback |
| Fail-open em `useCanAccess` | idem | `VERIFIED_IN_AVAILABLE_CODE` | `src/hooks/useCanAccess.ts:13-16`, com `console.warn` explícito quando `cargo` está ausente |
| `AdminRouteGuard` delega a autorização inteiramente a `pode()` | não avaliado antes | `VERIFIED_IN_AVAILABLE_CODE` | `src/components/admin/AdminRouteGuard.tsx:34` — não há nenhuma chamada ao servidor para validar sessão/token neste componente; a decisão é 100% local |
| `ai-analyst`/`proxy-file-upload` sem `verify_jwt` | `CONFIRMED_UNAUTHENTICATED_BY_SOURCE_REVIEW` | `VERIFIED_IN_AVAILABLE_CODE` | `supabase/config.toml:3-7` |
| `proxy-file-upload` repassa para destino controlado pelo chamador | idem | `VERIFIED_IN_AVAILABLE_CODE`, **com correção de escopo**: o destino não é uma URL arbitrária de qualquer host — `supabase/functions/proxy-file-upload/index.ts:19,28` constrói `targetUrl = WEBHOOK_BASE + path`, onde `path` é livre mas o host é fixo (`n8n.serdial21.com/webhook`). Ainda é um relay não autenticado para **qualquer path sob esse host**, incluindo webhooks que não deveriam ser públicos, mas não é SSRF para a internet em geral. | idem |
| `useTickets.ts` sem token | `CONFIRMED_UNAUTHENTICATED_LEGACY_DEAD_CODE` | `VERIFIED_IN_AVAILABLE_CODE`, com **escopo morto maior do que o relatório indicava**: nenhuma chamada a `useTickets`/`TicketTable`/`TicketKanban`/`TicketFormDialog` existe em `AdminTickets.tsx` (a página realmente roteada); todo esse subconjunto de componentes está órfão, não apenas o hook | `src/pages/admin/AdminTickets.tsx` (sem import dos quatro); `src/hooks/useTickets.ts` (fetch sem header `Authorization` em nenhuma das quatro funções) |

### Correções ao relatório de terceiros (2026-09-21, parte 1)

Comparado ao código real, dois pontos do relatório de terceiros eram imprecisos e devem ser lidos com a ressalva abaixo, não como estavam registrados:

- **`ClientRouteGuard.tsx` não é "apenas visual".** O código real (`src/components/client/ClientRouteGuard.tsx:31-41`) chama `portalFetch('/portal/me-v2')` e desloga o usuário se a sessão for inválida — há verificação real contra o servidor antes de renderizar. O comentário do próprio arquivo (linha 16) é preciso: a proteção **dos dados** continua sendo a validação do token a cada chamada no n8n, não este guard — mas o guard em si não é decorativo.
- **Nem as três Edge Functions têm autenticação igualmente ausente.** `supabase/config.toml` só desliga `verify_jwt` para `ai-analyst` e `proxy-file-upload`. `proxy-webhook` (usada por `useAdminDashboard.ts`, `useImpostos.ts` e outros) não está no arquivo de config, portanto segue o padrão do Supabase de exigir um JWT válido para ser invocada — uma sessão Supabase autenticada, não necessariamente vinculada ao usuário/permissão do painel Serdial21, mas não é chamável anonimamente como as outras duas.

### Achado adicional: fail-open é comportamento especificado, não só bug de frontend

`PROMPT_PERMISSOES_N8N_MYSQL.md` (documento de especificação de backend do próprio Sistema A, na raiz do repositório) descreve o desenho pretendido das tabelas `permissoes_funcionario_modulos`, `permissoes_funcionario_clientes` e `permissoes_cliente_portal`, e afirma explicitamente (linha 120): *"Se um funcionário não tem registro nesta tabela, por padrão ele tem acesso a **todos** os clientes."* Isso muda a leitura de `SG-03`: o fail-open não é apenas uma escolha defensiva do código React — é a semântica de backend **especificada**, que o frontend replica fielmente. Se essa especificação foi implementada como escrita, o problema não se resolve só corrigindo o frontend; precisa de uma decisão explícita de política (deny-by-default) no desenho do backend também. O documento não prova o que o n8n/MySQL realmente fazem hoje — é a especificação de implementação, não uma evidência de runtime — mas eleva a prioridade de esclarecer isso no verification package.

Este documento também fornece a primeira evidência de **schema MySQL pretendido** (não confirmado em produção) para as três tabelas de permissões, incluindo chaves, índices e FKs para `funcionarios`/`clientes` — avança parcialmente o item CHP-04, ainda sem satisfazer "schema-only read-only" de um banco real.

### Conclusão da Phase 09B nesta atualização

A disponibilização do código-fonte real avança significativamente CHP-01 e fortalece CHP-06 de evidência de terceiros para evidência direta, mas **não** resolve os bloqueadores que dependem do lado n8n/MySQL (CHP-02, CHP-04 completo, CHP-11, CHP-12, CHP-13, CHP-16) nem substitui testes em homologação. A conclusão desta parte permanece:

**PHASE 09B — SYSTEM A RUNTIME VERIFICATION: BLOCKED** (evidência de frontend fortalecida; evidência de backend/n8n/MySQL ainda ausente)

**INTEGRATION: NO_GO**

Esta conclusão é superada pela atualização seguinte, que traz o lado n8n/MySQL.

## Atualização 2026-09-22 — pacote de verificação real recebido (n8n + MySQL)

O dono do produto forneceu 60 exports de workflows n8n (pasta local, todos `active: true`) e 30 exports de estrutura MySQL (pasta local; chegaram com dados reais, que foram removidos antes de qualquer leitura — ver `SYSTEM_A_SECURITY_GAPS.md`). Isso satisfaz os itens 2 e 4 do "verification package" de `CONNECT_HUB_PREREQUISITES.md` (source do frontend já tínhamos desde 2026-09-21; agora também workflows n8n e schema MySQL). Ainda faltam os itens 1 (URL de homologação isolada), 3 (fixtures de Drive), 6 (matriz de credenciais) e 7 (test runner contra HOM) — nenhum teste de escrita foi executado, nenhuma homologação foi criada.

### O que passa de `NOT_VERIFIABLE`/`RUNTIME_VERIFICATION_REQUIRED` para `VERIFIED_IN_AVAILABLE_CODE`

- **Autorização fail-closed**: `FAIL` confirmado — o próprio workflow de permissões (`admin/permissoes/cliente`) inicia todos os módulos como `true` e só nega com uma linha explícita `permitido=0`. Não é mais leitura de frontend, é a lógica do backend. Detalhe completo e achados relacionados (SG-07 a SG-15) em `SYSTEM_A_SECURITY_GAPS.md`.
- **Padrão `success/message/data`**: os workflows autenticados retornam esse formato de forma consistente nos casos que inspecionei (login, permissões, update de item, upload) — mais consistente do lado servidor do que o frontend, que em alguns pontos ignora o campo `success` (achado já registrado).
- **Sessão/expiração**: `expira_em > NOW()` é checado no backend em todos os workflows autenticados lidos — a sessão TEM validade e ela é aplicada. `SESSION MODEL` sobe de `PARTIAL` para `VERIFIED_IN_AVAILABLE_CODE` nesse aspecto específico.
- **Revogação de sessão (`LOGOUT REVOCATION`)**: deixa de ser `GAP` genérico e passa a `CONFIRMED_INCONSISTENT` — o campo existe e é checado (`revogado_em IS NULL`) em alguns workflows (update de item, upload de documento) mas não em outro que também valida sessão (`admin/permissoes/cliente`).
- **Upload `/admin/upload-documento-cliente`**: deixa de ser `MISSING`. O workflow existe, está ativo e implementa o fluxo completo (Drive + `inbox_documentos`/`entregas_master`/`impostos_obrigacoes`/`honorarios_parcelas`). `CHP-17`/`IR-P0-09` são dados como resolvidos do lado do Sistema A.
- **Update Kanban "sucesso sem persistir"**: deixa de ser apenas um relato histórico. Causa raiz identificada no workflow `admin-update-item-v5`: a resposta de sucesso não verifica `affectedRows`, então um `UPDATE ... WHERE id=X` que não encontra a linha ainda responde `{"success":true}`. `CHP-12` permanece bloqueador, mas agora com diagnóstico preciso e correção pequena e localizada.
- **Auditoria**: `logs_auditoria` deixa de ser `UNKNOWN` — existe, tem ~1170 linhas reais e é escrita por 18 dos 60 workflows. Mas login, permissões, update de item do Kanban e upload de documento — justamente as ações mais sensíveis — não escrevem nela. `AUDIT` passa a `PARTIAL_COVERAGE_CONFIRMED`.
- **MySQL schema**: `MYSQL SCHEMA VERIFIED` passa de `NO` para `YES` para as 30 tabelas exportadas (estrutura). Tabelas centrais confirmadas: `clientes`, `funcionarios`, `tickets_master`, `tasks_master`, `inbox_documentos`, `logs_auditoria`, `permissoes_funcionario_modulos`, `permissoes_cliente_portal`, `security_sessoes_funcionarios`, `security_credenciais` (vazia nesta exportação) e mais 20 tabelas operacionais (honorários, impostos, certidões, agenda).
- **N8N runtime**: `N8N RUNTIME INSPECTED` passa de `PARTIAL` para `VERIFIED_IN_AVAILABLE_CODE` — todos os 60 workflows exportados estão `active: true`, incluindo versões antigas simultâneas ao lado das novas (ex.: `admin-delete-item-v1` e `v3` ambos ativos). Isso confirma que os conflitos de versão do `CANONICAL_OPERATIONAL_API_MAP.md` não são código morto: cada versão é uma rota realmente atendida hoje.

### O que continua sem verificação

- Nenhum teste real de escrita foi executado (create→read→update→read→delete sintético) — a causa raiz do CHP-12 foi lida no código, não observada em execução.
- CORS/OPTIONS não foram exercitados por chamada real.
- Ambiente de homologação isolado continua `MISSING`.
- Dados reais de clientes/funcionários não foram lidos (removidos antes da leitura); portanto o *conteúdo* de auditoria, tickets, honorários etc. não foi inspecionado, só a estrutura.

### Conclusão vigente (supera todas as anteriores)

O lado n8n/MySQL deixou de ser a lacuna de evidência: agora sabemos, com código real, exatamente o que falha e por quê (fail-open no backend, hashing de senha fraco, geração de token não criptográfica, consultas SQL não parametrizadas, revogação de sessão inconsistente, cobertura de auditoria incompleta — detalhes em `SYSTEM_A_SECURITY_GAPS.md`). Isso é progresso real, mas na direção de *confirmar* bloqueadores, não de removê-los — a evidência nova é majoritariamente mais grave do que a suposição anterior, não mais branda. Dois itens são dados como resolvidos (upload de documento existe; causa raiz do bug do Kanban identificada). Segurança de produção do Sistema A (SG-07 a SG-12) deve ser corrigida antes de qualquer dado real trafegar entre os sistemas. Homologação isolada, fixtures de Drive, matriz de credenciais e testes de escrita continuam ausentes.

**PHASE 09B — SYSTEM A RUNTIME VERIFICATION: BLOCKED** (evidência completa de frontend + backend/n8n/MySQL; bloqueadores confirmados com causa raiz, não mais por ausência de prova)

**SYSTEM A: NOT_READY_FOR_CONNECT_HUB_MVP — mas com punch list claro e corrigível**

**INTEGRATION: NO_GO**
