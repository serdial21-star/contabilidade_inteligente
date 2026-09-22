# Canonical Operational API Map

Status do mapa: `PARTIAL`. “Canônico” aqui significa inventário de decisão, não confirmação runtime. Nenhum endpoint funcional foi chamado. O status adicional `NOT_VERIFIABLE` é usado porque o código/exports do Sistema A não foram fornecidos; seria incorreto marcar `ACTIVE_CODE_ONLY` sem código ou `ACTIVE_VERIFIED` sem execução.

Base documentada: `https://n8n.serdial21.com/webhook`. A raiz pública do n8n respondeu em 2026-09-15; isso não valida os paths abaixo.

| Path | Método | Versão | Frontend consumer documentado | Workflow documentado | Auth | Request / response documentados | Status |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `/portal-serdial-v2` | POST | v2 | `Login.tsx` | `portal-serdial-v2` | pública → token cliente | credenciais → `success/data` | `NOT_VERIFIABLE` |
| `/portal/me-v2` | POST | v2 | `Dashboard.tsx` | não congelado | Bearer cliente | token → perfil | `NOT_VERIFIABLE` |
| `/portal/solicitar-senha` | POST | unversioned | `EsqueciSenha.tsx` | `reset-senha` | pública | e-mail → mensagem segura | `NOT_VERIFIABLE` |
| `/portal/redefinir-senha` | POST | unversioned | `RedefinirSenha.tsx` | `reset-senha` | reset token | nova senha → resultado | `NOT_VERIFIABLE` |
| `/portal/meus-chamados-v2` | POST | v2 | `Chamados.tsx`, `TicketHistory.tsx` | `portal-tickets` | Bearer cliente | filtros → tickets | `NOT_VERIFIABLE` |
| `/portal/abrir-ticket-v2` | POST | v2 | `HelpdeskTicketForm.tsx` | `portal-tickets` | Bearer cliente | ticket → referência | `NOT_VERIFIABLE` |
| `/portal/detalhe-chamado` | POST | unversioned | `TicketDetailDrawer.tsx` | `portal-tickets` | Bearer cliente | ref → detalhe | `NOT_VERIFIABLE` |
| `/portal/complementar-chamado` | POST | unversioned | `TicketDetailDrawer.tsx` | `portal-tickets` | Bearer cliente | ref/complemento → resultado | `NOT_VERIFIABLE` |
| `/portal/meus-documentos-v2` | POST | v2 | `Biblioteca.tsx`, `MeusDocumentos.tsx` | `portal-docs` | Bearer cliente | filtros → documentos | `NOT_VERIFIABLE` |
| `/portal/detalhe-documento` | POST | unversioned | `DocumentDetailDrawer.tsx` | `portal-docs` | Bearer cliente | ref → metadata | `NOT_VERIFIABLE` |
| `/portal/complementar-documento` | POST | unversioned | `DocumentDetailDrawer.tsx` | `portal-docs` | Bearer cliente | FormData/ref → resultado | `NOT_VERIFIABLE` |
| `/portal/receber-arquivo-v2` | POST FormData | v2 | `EnviarDocumentos.tsx` | não congelado | Bearer cliente | arquivo/metadata → receipt | `NOT_VERIFIABLE` |
| `/portal/certidoes-v2` | POST | v2 | documentos tabs | `repositorios` | Bearer cliente | filtros → lista | `NOT_VERIFIABLE` |
| `/portal/livros-contabeis-v2` | POST | v2 | documentos tabs | `repositorios` | Bearer cliente | filtros → lista | `NOT_VERIFIABLE` |
| `/portal/obrigacoes-v2` | POST | v2 | documentos tabs | `repositorios` | Bearer cliente | filtros → lista | `NOT_VERIFIABLE` |
| `/portal/impostos-v2` | POST | v2 | `useImpostos.ts` | `impostos-v2` | Bearer cliente | filtros → impostos | `NOT_VERIFIABLE` |
| `/portal/pagar-imposto-v2` | POST | v2 | não identificado | não congelado | Bearer cliente | ref → resultado | `NOT_VERIFIABLE` |
| `/portal/honorarios-v2` | POST | v2 | `Honorarios.tsx` | `honorarios-portal` | Bearer cliente | filtros → honorários | `NOT_VERIFIABLE` |
| `/cliente/*` equivalentes | misto | v2/unversioned | diagnóstico antigo | desconhecido | token cliente | desconhecido | `LEGACY` provável; conflito de namespace |
| `/admin/login-v2` | POST | v2 | `AdminLogin.tsx` | `admin-login-v2` | pública → token admin | credenciais → `success/data` | `NOT_VERIFIABLE` |
| `/admin/solicitar-senha` | POST | unversioned | `AdminEsqueciSenha.tsx` | `reset-senha` | pública | e-mail → mensagem segura | `NOT_VERIFIABLE` |
| `/admin-dashboard-v1` | POST | v1 | contexto antigo | `dashboard-v1` | Bearer admin | filtros → aggregates | `LEGACY` provável |
| `/admin-dashboard-v2` | POST | v2 | `useAdminDashboard.ts` | `dashboard-v2` | Bearer admin | filtros → aggregates | `CONFLICTING` — atividade não comprovada |
| `/admin-agenda-v1` | POST | v1 | contexto antigo | `agenda-v1` | Bearer admin | período → items | `LEGACY` provável |
| `/admin-agenda-v2` | POST | v2 | agenda documentada | `agenda-v2` | Bearer admin | período → items | `CONFLICTING` — atividade não comprovada |
| `/admin/clientes-v2` | POST | v2 | `useClientes`, `PermissoesManager.tsx` | `clientes-v2` | Bearer admin | filtros → clientes | `NOT_VERIFIABLE` |
| `/admin/novo-cliente-v2` | POST | v2 | cadastro cliente | `novo-cliente-v2` | Bearer admin | cliente → ref | `NOT_VERIFIABLE` |
| `/admin/equipe-v2` | POST | v2 | `AdminEquipe.tsx` | `equipe-v2` | Bearer admin | filtros → equipe | `CONFLICTING` com funcionários |
| `/admin/funcionarios` | POST | unversioned | `useFuncionarios.ts` | desconhecido | Bearer admin | filtros → funcionários | `LEGACY`/`CONFLICTING` |
| `/admin/novo-funcionario` | POST | unversioned | `FuncionarioFormDialog.tsx` | `equipe-v2` alegado | Bearer admin | funcionário → ref | `NOT_VERIFIABLE` |
| `/admin/editar-funcionario` | POST | unversioned | `FuncionarioFormDialog.tsx` | `equipe-v2` alegado | Bearer admin | funcionário → resultado | `NOT_VERIFIABLE` |
| `/admin/permissoes/funcionario` | POST | unversioned | `usePermissoes.ts` | `permissoes-funcionario` | Bearer admin | funcionário → permissões | `NOT_VERIFIABLE` |
| `/admin/permissoes/funcionario/salvar` | POST | unversioned | `PermissoesManager.tsx` | `permissoes-funcionario` | Bearer admin | permission set → resultado | `NOT_VERIFIABLE` |
| `/admin/permissoes/cliente` | POST | unversioned | `useClientPermissoes.ts` | não congelado | Bearer admin | cliente → permissões | `NOT_VERIFIABLE` |
| `/admin/permissoes/cliente/salvar` | POST | unversioned | `PermissoesManager.tsx` | não congelado | Bearer admin | permission set → resultado | `NOT_VERIFIABLE` |
| `/admin/tickets` (unversioned) | GET/POST/PUT/DELETE | unversioned | `useTickets.ts` (órfão) | `admin/tickets` alegado | **nenhuma** — `VERIFIED_IN_AVAILABLE_CODE` (2026-09-21): nenhuma chamada `fetch` em `useTickets.ts` inclui header `Authorization` | criar/atualizar/excluir ticket → resultado | `VERIFIED_UNAUTHENTICATED_DEAD_CODE` (2026-09-21) — `AdminTickets.tsx` (página roteada) não importa `useTickets`, `TicketTable`, `TicketKanban` nem `TicketFormDialog`; todo esse subconjunto está órfão, escopo maior que o relatório de terceiros indicava. Candidato a remoção completa, não só a "não reutilizar" |
| `/admin/tickets-v2` | POST | v2 | `AdminTickets.tsx` | `tickets-v2` | Bearer admin | filtros → tickets | `NOT_VERIFIABLE`; confirmado como caminho ativo da UI atual por revisão de terceiros (2026-09-21) |
| `/admin/responder-ticket-v2` | POST | v2 | `AdminTickets.tsx` | `tickets-v2` | Bearer admin | ref/resposta → resultado | `NOT_VERIFIABLE` |
| `/admin/documentos-v2` | POST | v2 | `AdminDocumentos.tsx` | `documentos-v2` | Bearer admin | filtros → inbox | `NOT_VERIFIABLE` |
| `/admin/enviar-inbox` | POST | unversioned | documento admin | não congelado | Bearer admin | metadata/arquivo → receipt | `NOT_VERIFIABLE` |
| `/admin/upload-documento-cliente` | POST FormData | unversioned | `AdminUploadDocumentosForm.tsx:183` | documentado como inexistente | Bearer admin | arquivo/cliente → receipt | `MISSING`, confirmado por revisão de código de terceiros em 2026-09-21 (chamada existe no frontend, workflow n8n correspondente ainda não confirmado) |
| `/admin/upload-documentos` | rota de tela, não webhook | — | route registry antigo | — | guard documentos | — | `LEGACY`/não é API |
| `/admin/impostos` | POST | unversioned | `useImpostos.ts:110,145` (`useImpostosAdmin`, via proxy-webhook) | `impostos` | Bearer admin | filtros → impostos | `VERIFIED_IN_AVAILABLE_CODE` (2026-09-21): ativamente usado por `AdminImpostos.tsx` para listagem/ações |
| `/admin/impostos-v2` | POST | v2 | `AdminImpostos.tsx:191` (fetch direto, fora do hook) | `impostos-v2` alegado | Bearer admin | filtros → impostos | `VERIFIED_IN_AVAILABLE_CODE` (2026-09-21): a MESMA página usa as duas versões simultaneamente para operações diferentes — não é migração em andamento, é um conflito real e atual, não apenas dossiê |
| `/admin/novo-imposto` | POST | unversioned | `useImpostos.ts` | `impostos` | Bearer admin | imposto → ref | `CONFLICTING` |
| `/admin/novo-imposto-v2` | POST | v2 | recomendação/dossiê | não comprovado | Bearer admin | imposto → ref | `CONFLICTING` |
| `/admin/honorarios-v2` | POST | v2 | `AdminHonorarios.tsx` | `honorarios-v2` | Bearer admin | filtros → contratos | `NOT_VERIFIABLE` |
| `/admin/honorarios-parcelas-v2` | POST | v2 | `AdminHonorarios.tsx` | `honorarios-v2` | Bearer admin | contrato → parcelas | `NOT_VERIFIABLE` |
| `/admin/honorarios-servicos-v2` | POST | v2 | diagnóstico | não congelado | Bearer admin | filtros → serviços | `NOT_VERIFIABLE` |
| `/admin/fiscal/upload-xml` | POST | unversioned | `AdminFiscal.tsx` | `fiscal-ia` | Bearer admin | XML → resultado | `NOT_VERIFIABLE` |
| `/admin/fiscal/listar` | POST | unversioned | `AdminFiscal.tsx` | `fiscal-ia` | Bearer admin | filtros → lista | `NOT_VERIFIABLE` |
| `/admin/fiscal/conferir` | POST | unversioned | `AdminFiscal.tsx` | `fiscal-ia` | Bearer admin | ref/ação → resultado | `NOT_VERIFIABLE` |
| `/admin-kanban-v3` | POST | v3 | `useTasks.ts:94-97` | `kanban-v3` | Bearer admin | filtros → items | `CONFLICTING` contract set; chamada confirmada ativa por revisão de terceiros 2026-09-21, simultânea a `create/update-v5` (não é migração sequencial) |
| `/admin-create-item-v3` | POST | v3 | diagnóstico antigo | `create-v3` alegado | Bearer admin | item → ref | `LEGACY` provável |
| `/admin-create-item-v5` | POST | v5 | `useTasks.ts:94-97` | `create-v5` | Bearer admin | item → ref | `CONFLICTING` — chamada de frontend confirmada 2026-09-21; persistência/efeito no workflow ainda não verificado |
| `/admin-update-item-v1` | POST | v1 | dossiê técnico | `update-v1` | Bearer admin | item/status → resultado | `CONFLICTING` — persistência não provada; não é o caminho chamado pelo frontend atual (ver v5) |
| `/admin-update-item-v5` | POST | v5 | `useTasks.ts:94-97` | `update-v5` | Bearer admin | item/status → resultado | `CONFLICTING` — chamada de frontend confirmada 2026-09-21; persistência ainda **não provada** (CHP-12 permanece `CONFIRMED_BLOCKER`) |
| `/admin-delete-item-v3` | POST | v3 | `useTasks.ts:94-97` | `delete-v3` | Bearer admin | item ref → resultado | `NOT_VERIFIABLE`; chamada confirmada ativa por revisão de terceiros 2026-09-21 |
| `/admin/atalhos` | POST | unversioned | `useAtalhos.ts` | `atalhos` | Bearer admin | filtros → atalhos | `NOT_VERIFIABLE` |
| `/admin-clientes-options-v1` | POST | v1 | `useOptionsAPI.ts` | `options-v1` | Bearer admin | busca → options | `NOT_VERIFIABLE` |
| `/admin-funcionarios-options-v1` | POST | v1 | `useOptionsAPI.ts` | `options-v1` | Bearer admin | busca → options | `NOT_VERIFIABLE` |
| `/listar-arquivos` | não congelado | unversioned | não identificado | não congelado | desconhecida | desconhecido | `NOT_VERIFIABLE` |

## Conflitos restantes

Sete grupos permanecem sem resolução: dashboard v1/v2; agenda v1/v2; create v3/v5; update v1/v5 e persistência; impostos unversioned/v2; equipe/funcionários; `/cliente/*` versus `/portal/*`. Nenhuma nova versão deve ser criada. O freeze exige source tag do frontend, export dos workflows ativos e testes HOM.

**Atualização 2026-09-21** (fonte: `docs/integration-input/RELATORIO_VARREDURA_LOVABLE_20260921.md`, revisão de código de terceiros do frontend + 3 Supabase Edge Functions): nenhum dos sete conflitos é resolvido por completo, porque "endpoint chamado pelo frontend hoje" não prova "workflow correto/persistente no n8n" — mas o relatório reduz a incerteza de qual versão está de fato em uso:
- **create/update/delete de item (kanban):** confirmado que `useTasks.ts` chama simultaneamente `admin-kanban-v3`, `admin-delete-item-v3`, `admin-create-item-v5` e `admin-update-item-v5` — ou seja, v3 e v5 coexistem em produção, não é uma migração v3→v5 concluída. Isso é informação nova; nenhum dos três dossiês originais havia descrito coexistência.
- **impostos:** ambos os caminhos (`useImpostos.ts` unversioned e `AdminImpostos.tsx` `-v2`) aparecem como chamados no código — o relatório não indica qual é morto, ao contrário do achado equivalente em tickets (abaixo). Conflito permanece `CONFLICTING`, agora com maior detalhe.
- **tickets:** diferente dos demais, este conflito É esclarecido — o caminho unversioned (`useTickets.ts`) é código legado sem autenticação e a tela atual usa exclusivamente `-v2` (`AdminTickets.tsx`). Ver a linha `/admin/tickets` acima; candidato a decomissionamento formal no freeze, não apenas a "não reutilizar".
- **dashboard v1/v2, agenda v1/v2, equipe/funcionários, `/cliente/*` vs `/portal/*`:** não cobertos pelo relatório; permanecem exatamente como antes.

Nenhum destes itens libera o freeze (`CHP-03` continua `CONFIRMED_BLOCKER`); a evidência de código de terceiros não substitui o export dos workflows ativos exigido para fechar o inventário.

## Rotas de tela documentadas

O registry atual não foi fornecido. Rotas históricas: cliente `/login`, `/dashboard`, `/chamados`, `/documentos`, `/biblioteca`, `/meus-documentos`, `/honorarios`, `/impostos`; admin `/admin`, `/admin/clientes`, `/admin/tickets`, `/admin/entregas`, `/admin/documentos`, `/admin/equipe`, `/admin/configuracoes`, `/admin/impostos`, `/admin/honorarios`, `/admin/ferramentas-ia`, `/admin/atalhos`, `/admin/tarefas`, `/admin/agenda`, `/admin/upload-documentos`. Guards e chamadas permanecem `NOT_VERIFIABLE`.

## Critério para `ACTIVE_VERIFIED`

Exige simultaneamente: workflow ativo/export identificado; consumer no source tag; teste sintético em homologação; auth negativa; request/response capturados sem segredo; efeito lido após write quando aplicável. Nenhum endpoint atingiu esse nível na Phase 09B.
