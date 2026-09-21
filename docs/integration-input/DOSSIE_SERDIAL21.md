# Dossiê Técnico e Operacional — Portal do Cliente Serdial21

> Documento de auditoria gerado **sem alterações de código**. Objetivo: registrar o estado atual, riscos, pendências e a sequência segura para finalizar a versão 1.0.

---

## 1. Resumo Executivo

**O que é:** Plataforma SaaS contábil composta por dois ambientes integrados:
- **Portal do Cliente** (`/login`, `/dashboard`, `/biblioteca`, `/chamados`, `/impostos`, `/honorarios`)
- **Painel Administrativo** Serdial21 (`/admin/*`) usado pela equipe interna.

**Objetivo de negócio:** centralizar comunicação, documentos, obrigações fiscais, honorários e tickets entre o escritório contábil Serdial21 e seus clientes, eliminando trocas dispersas por e-mail/WhatsApp.

**Módulos existentes (frontend):** Autenticação cliente/admin, Dashboard, Biblioteca (documentos/entregas/certidões/livros/obrigações), Chamados/Tickets, Impostos, Honorários, Clientes, Equipe, Permissões, Atalhos, Ferramentas IA, Central de Operações (Kanban), Upload de Documentos pelo admin.

**Estágio atual:** Frontend em estágio **avançado (≈85%)** com todas as telas principais implementadas. Backend (n8n + MySQL + Drive) **parcialmente entregue**: vários workflows operacionais, porém com **inconsistências de versionamento (v1/v2/v3/v5)**, endpoints chamados pelo frontend sem confirmação de existência no n8n, e o webhook crítico `/admin/upload-documento-cliente` ainda **não foi criado** (apenas documentado).

**Maiores riscos para finalização:**
1. Webhook de upload de documentos admin → cliente **ausente no n8n** (bloqueador).
2. Endpoints versionados sem mapa oficial: risco de chamadas para rotas inexistentes/legadas.
3. CORS e `Respond to Webhook` não verificados em todos os workflows.
4. Permissões podem retornar vazio e bloquear o dashboard (problema histórico).
5. Inconsistência entre módulo de **Entregas** (rota removida) e tabela `entregas_master` ainda referenciada no backlog.
6. Falta de testes E2E e de logs estruturados.

---

## 2. Mapa da Arquitetura

```
┌──────────────┐    HTTPS     ┌───────────────────┐   HTTPS    ┌────────────────────┐
│  Navegador   │ ───────────▶ │  Frontend React   │ ─────────▶ │   n8n self-hosted  │
│ Cliente/Admin│              │ Vite + Vercel     │   Webhook  │ n8n.serdial21.com  │
└──────────────┘              │ serdial21.com     │            └─────────┬──────────┘
                              └────────┬──────────┘                      │
                                       │                                 │
                                       │ (proxy-webhook,                 ▼
                                       │  proxy-file-upload,    ┌────────────────┐
                                       │  ai-analyst)           │ MySQL Hostinger│
                                       ▼                        │ (DB principal) │
                              ┌──────────────────┐              └────────────────┘
                              │ Supabase Edge Fn │                       │
                              │ (Lovable Cloud)  │                       ▼
                              └──────────────────┘            ┌────────────────────┐
                                       │                     │ Google Drive (docs)│
                                       ▼                     │ SMTP Hostinger     │
                              ┌──────────────────┐           │ Z-API (WhatsApp)   │
                              │ Supabase Storage │           └────────────────────┘
                              │ (logos clientes) │
                              └──────────────────┘
```

**Tokens e sessão:**
| Ambiente | Storage | Chave | Origem |
|---|---|---|---|
| Cliente | `localStorage` | `auth_token` | `/portal-serdial-v2` |
| Admin   | `localStorage` | `admin_auth_token` + `admin_user` | `/admin/login-v2` |

**Validação:** todos os webhooks `v2` esperam header `Authorization: Bearer <token>`. O backend consulta `security_sessoes_*` para validar expiração e identificar usuário (regra de auditoria: nunca confiar em `user.id` do body).

**Módulos públicos (sem Bearer):** `/portal-serdial-v2` (login), `/portal/solicitar-senha`, `/portal/redefinir-senha`, `/admin/login-v2`, `/admin/solicitar-senha`.

**Edge functions Supabase em uso:**
- `proxy-webhook` — proxy genérico portal cliente
- `proxy-file-upload` — uploads multipart do cliente
- `ai-analyst` — Lovable AI (Gemini) para ferramentas IA

---

## 3. Mapa do Frontend

### Rotas registradas (`src/App.tsx`)

| Rota | Página | Guarda | Observação |
|---|---|---|---|
| `/` | Redirect → `/login` | — | |
| `/login` | `Login.tsx` | público | Portal cliente |
| `/dashboard` | `Dashboard.tsx` | — (deveria ter guard) | **Risco:** sem `ClientRouteGuard` |
| `/chamados` | `Chamados.tsx` | — | idem |
| `/documentos` | `EnviarDocumentos.tsx` | — | idem |
| `/biblioteca` | `Biblioteca.tsx` | — | Recebe redirect `/meus-documentos` |
| `/meus-documentos` | Redirect → `/biblioteca` | — | OK |
| `/honorarios` | `Honorarios.tsx` | — | |
| `/impostos` | `Impostos.tsx` | — | |
| `/esqueci-senha`, `/redefinir-senha` | público | — | |
| `/admin/login` | `AdminLogin.tsx` | público | |
| `/admin/esqueci-senha` | `AdminEsqueciSenha.tsx` | público | |
| `/admin` | `AdminDashboard.tsx` | `AdminRouteGuard(dashboard)` | Hub Central de Operações |
| `/admin/clientes` | `AdminClientes.tsx` | Guard `clientes` | |
| `/admin/tickets` | `AdminTickets.tsx` | Guard `tickets` | |
| `/admin/entregas` | Redirect → `/admin` | — | Módulo removido |
| `/admin/documentos` | `AdminDocumentos.tsx` | Guard `documentos` | Inbox |
| `/admin/equipe` | `AdminEquipe.tsx` | Guard + role Admin | |
| `/admin/configuracoes` | `AdminConfiguracoes.tsx` | Guard + role Admin | |
| `/admin/impostos` | `AdminImpostos.tsx` | Guard `impostos` | |
| `/admin/honorarios` | `AdminHonorarios.tsx` | Guard `honorarios` | |
| `/admin/ferramentas-ia` | `AdminFerramentasIA.tsx` | Guard `ferramentas_ia` | |
| `/admin/atalhos` | `AdminAtalhos.tsx` | Guard `atalhos` | |
| `/admin/tarefas`, `/admin/agenda` | Redirect → `/admin` | — | Unificados na Central |
| `/admin/upload-documentos` | `AdminUploadDocumentos.tsx` | Guard `documentos` | **Aguardando webhook n8n** |
| `*` | `NotFound.tsx` | — | |

### Contextos / Hooks principais

| Item | Arquivo | Função |
|---|---|---|
| `ClientAuthProvider` | `contexts/ClientAuthContext.tsx` | Sessão cliente em localStorage |
| `AdminAuthProvider` | `contexts/AdminAuthContext.tsx` | Sessão admin + `adminFetch` |
| `ThemeProvider` | `contexts/ThemeContext.tsx` | Light/Dark |
| `useCanAccess` | `hooks/useCanAccess.ts` | RBAC por cargo (fallback permissivo) |
| `usePermissoes` | `hooks/usePermissoes.ts` | Permissões granulares por módulo |
| `useClientPermissoes` | `hooks/useClientPermissoes.ts` | Permissões por cliente |
| `useTasks` / `useTickets` / `useImpostos` / `useFuncionarios` / `useClientes` / `useAgenda` / `useAdminDashboard` / `useAtalhos` / `useListas` / `useOptionsAPI` | `hooks/*` | Wrappers de APIs n8n |

### Helpers de API

- `src/lib/apiClient.ts` — `portalFetch`, `getAuthHeaders`, `getAuthToken/setAuthToken/clearAuthToken` (portal cliente, via Supabase edge function `proxy-webhook`).
- `src/contexts/AdminAuthContext.tsx` — `adminFetch` (admin, direto para `https://n8n.serdial21.com/webhook`).
- `src/lib/kanbanContract.ts` — normalização de payload das operações.

### LocalStorage / SessionStorage

| Chave | Origem | Conteúdo |
|---|---|---|
| `auth_token` | apiClient | Bearer cliente |
| `client_user` | ClientAuthContext | Perfil cliente |
| `admin_auth_token` | AdminAuthContext | Bearer admin |
| `admin_user` | AdminAuthContext | Perfil admin |

### Variáveis de ambiente / endpoints hardcoded

- `N8N_BASE = 'https://n8n.serdial21.com/webhook'` **hardcoded** em `AdminAuthContext.tsx` (risco: dificulta swap dev/prod).
- Edge function path `'proxy-webhook'` hardcoded em `apiClient.ts`.
- `.env` (Lovable) provê `VITE_SUPABASE_URL`, `VITE_SUPABASE_PUBLISHABLE_KEY`, `VITE_SUPABASE_PROJECT_ID`.

### Tabela Tela × Endpoint

| Tela / Componente | Arquivo | Endpoint | Método | Bearer | Status aparente |
|---|---|---|---|---|---|
| Login cliente | `pages/Login.tsx` | `/portal-serdial-v2` | POST | não | OK |
| Esqueci senha (cliente) | `pages/EsqueciSenha.tsx` | `/portal/solicitar-senha` | POST | não | Precisa testar |
| Redefinir senha (cliente) | `pages/RedefinirSenha.tsx` | `/portal/redefinir-senha` | POST | não | Precisa testar |
| Dashboard cliente | `pages/Dashboard.tsx` | `/portal/me-v2` | POST | sim | Precisa testar |
| Biblioteca / Meus Docs | `pages/Biblioteca.tsx`, `MeusDocumentos.tsx`, `EnviarDocumentos.tsx` | `/portal/meus-documentos-v2` | POST | sim | OK |
| Certidões / Livros / Obrigações | `components/documentos/*Tab.tsx` | `/portal/certidoes-v2`, `/portal/livros-contabeis-v2`, `/portal/obrigacoes-v2` | POST | sim | Precisa testar |
| Impostos cliente | `hooks/useImpostos.ts` | `/portal/impostos-v2` | POST | sim | Precisa testar |
| Honorários cliente | `pages/Honorarios.tsx` | `/portal/honorarios-v2` | POST | sim | OK |
| Chamados cliente — lista | `pages/Chamados.tsx`, `components/TicketHistory.tsx` | `/portal/meus-chamados-v2` | POST | sim | OK |
| Chamados — abrir | `components/HelpdeskTicketForm.tsx` | `/portal/abrir-ticket-v2` | POST | sim | OK |
| Chamados — detalhe/responder | `components/TicketDetailDrawer.tsx` | `/portal/detalhe-chamado`, `/portal/complementar-chamado` | POST | sim | Precisa testar |
| Documento — detalhe/complementar | `components/DocumentDetailDrawer.tsx` | `/portal/detalhe-documento`, `/portal/complementar-documento` | POST | sim | Precisa testar |
| Login admin | `pages/admin/AdminLogin.tsx` | `/admin/login-v2` | POST | não | OK |
| Esqueci senha admin | `pages/admin/AdminEsqueciSenha.tsx` | `/admin/solicitar-senha` | POST | não | Precisa testar |
| Dashboard admin / Central Op. | `hooks/useAdminDashboard.ts` | `/admin-dashboard-v2` | POST | sim | **Inconsistente** (esperado v1 conforme contexto, frontend chama v2) |
| Clientes — listar | `components/admin/PermissoesManager.tsx` e `useClientes` | `/admin/clientes-v2` | POST | sim | OK |
| Equipe — listar | `pages/admin/AdminEquipe.tsx`, PermissoesManager | `/admin/equipe-v2` | POST | sim | OK |
| Equipe — criar/editar funcionário | `components/admin/FuncionarioFormDialog.tsx` | `/admin/novo-funcionario`, `/admin/editar-funcionario` | POST | sim | Precisa testar |
| Equipe (alt.) | `hooks/useFuncionarios.ts` | `/admin/funcionarios` | POST | sim | **Possível duplicidade vs `/admin/equipe-v2`** |
| Permissões | `hooks/usePermissoes.ts`, `PermissoesManager.tsx` | `/admin/permissoes/funcionario[/salvar]`, `/admin/permissoes/cliente[/salvar]` | POST | sim | OK (histórico de tela branca quando vazio) |
| Tickets admin | `pages/admin/AdminTickets.tsx` | `/admin/tickets-v2`, `/admin/responder-ticket-v2` | POST | sim | OK |
| Documentos (Inbox) admin | `pages/admin/AdminDocumentos.tsx` | `/admin/documentos-v2` | POST | sim | OK |
| Impostos admin | `hooks/useImpostos.ts` | `/admin/impostos` (+ `/admin/novo-imposto` esperado) | POST | sim | **Inconsistente** (sem sufixo `-v2`) |
| Honorários admin | `pages/admin/AdminHonorarios.tsx` | `/admin/honorarios-v2`, `/admin/honorarios-parcelas-v2` | POST | sim | OK |
| Fiscal (IA) | `pages/admin/AdminFiscal.tsx` | `/admin/fiscal/upload-xml`, `/admin/fiscal/listar`, `/admin/fiscal/conferir` | POST | sim | Precisa testar |
| Central Op. — CRUD | `hooks/useTasks.ts` | `/admin-kanban-v3`, `/admin-create-item-v5`, `/admin-update-item-v1`, `/admin-delete-item-v3` | POST | sim | **Mix de versões** (risco) |
| Atalhos | `hooks/useAtalhos.ts` | `/admin/atalhos` | POST | sim | Precisa testar |
| Options (selects dinâmicos) | `hooks/useOptionsAPI.ts` | `/admin-clientes-options-v1`, `/admin-funcionarios-options-v1` | POST | sim | OK |
| **Upload documento admin → cliente** | `components/admin/AdminUploadDocumentosForm.tsx` | `/admin/upload-documento-cliente` | POST FormData | sim | **AUSENTE no n8n** |

---

## 4. Mapa das Integrações n8n

| Módulo | Endpoint | Método | Workflow n8n | Tabelas | Status | Observações |
|---|---|---|---|---|---|---|
| Login cliente | `/portal-serdial-v2` | POST | portal-serdial-v2 | `clientes`, `clientes_emails_autorizados`, `security_sessoes_clientes`, `log_tentativas_login` | OK aparente | Verificar rate limit |
| Login admin | `/admin/login-v2` | POST | admin-login-v2 | `funcionarios`, `security_sessoes_funcionarios` | OK aparente | |
| Permissões funcionário | `/admin/permissoes/funcionario[/salvar]` | POST | permissoes-funcionario | `permissoes_funcionario_modulos`, `permissoes_funcionario_clientes` | Requer correção | Retorno vazio causa tela branca |
| Cadastro cliente | `/admin/novo-cliente-v2` | POST | novo-cliente-v2 | `clientes`, `clientes_emails_autorizados` + Drive + SMTP | Precisa testar | Cria pastas 00_INBOX..99_DIVERSOS |
| Listagem clientes | `/admin/clientes-v2` | POST | clientes-v2 | `clientes` | OK aparente | |
| Equipe | `/admin/equipe-v2`, `/admin/novo-funcionario`, `/admin/editar-funcionario` | POST | equipe-v2 | `funcionarios` | Precisa testar | Validar duplicidade e-mail |
| Equipe (legado) | `/admin/funcionarios` | POST | ? | `funcionarios` | Duplicado/legado | Avaliar remoção em `useFuncionarios.ts` |
| Impostos admin | `/admin/impostos`, `/admin/novo-imposto` | POST | impostos | `impostos_obrigacoes`, `catalogo_obrigacoes` + Drive | Inconsistente | Frontend usa `/admin/impostos` sem `-v2` |
| Impostos cliente | `/portal/impostos-v2` | POST | impostos-v2 | `impostos_obrigacoes` | Precisa testar | |
| Agenda | `/admin-agenda-v1`, `/admin-agenda-v2` | POST | agenda-v1, agenda-v2 | `impostos_obrigacoes`, `tasks_master`, `tickets_master`, `entregas_master` | Duplicado | Avaliar substituição v1→v2 |
| Dashboard admin | `/admin-dashboard-v1`, `/admin-dashboard-v2` | POST | dashboard-v1/v2 | múltiplas | Inconsistente | Frontend chama `v2`; confirmar que está ativo |
| Tickets admin | `/admin/tickets-v2`, `/admin/responder-ticket-v2` | POST | tickets-v2 | `tickets_master` | OK aparente | |
| Documentos Inbox | `/admin/documentos-v2` | POST | documentos-v2 | `inbox_documentos` | OK aparente | |
| Central Operações | `/admin-kanban-v3`, `/admin-create-item-v5`, `/admin-update-item-v1`, `/admin-delete-item-v3` | POST | kanban-v3, create-v5, update-v1, delete-v3 | `tasks_master`, `tickets_master`, `impostos_obrigacoes`, `entregas_master` | Inconsistente | Versões misturadas |
| Honorários admin | `/admin/honorarios-v2`, `/admin/honorarios-parcelas-v2` | POST | honorarios-v2 | `honorarios_contratos`, `honorarios_parcelas`, `honorarios_servicos_avulsos`, `honorarios_recibos_sequencia` | OK aparente | + CRON |
| Honorários cliente | `/portal/honorarios-v2` | POST | honorarios-portal | idem | OK aparente | |
| Documentos cliente | `/portal/meus-documentos-v2`, `/portal/detalhe-documento`, `/portal/complementar-documento` | POST | portal-docs | `inbox_documentos`, `entregas_master` + Drive | Precisa testar | |
| Certidões / Livros / Obrigações | `/portal/certidoes-v2`, `/portal/livros-contabeis-v2`, `/portal/obrigacoes-v2` | POST | repositorios | tabelas específicas | Precisa testar | |
| Chamados cliente | `/portal/abrir-ticket-v2`, `/portal/meus-chamados-v2`, `/portal/detalhe-chamado`, `/portal/complementar-chamado` | POST | portal-tickets | `tickets_master` | OK aparente | |
| Atalhos | `/admin/atalhos` | POST | atalhos | tabela `atalhos` | Precisa testar | |
| Options | `/admin-clientes-options-v1`, `/admin-funcionarios-options-v1` | POST | options-v1 | `clientes`, `funcionarios` | OK aparente | |
| Senhas | `/portal/solicitar-senha`, `/portal/redefinir-senha`, `/admin/solicitar-senha` | POST | reset-senha | `security_*` + SMTP | Precisa testar | |
| Fiscal IA | `/admin/fiscal/upload-xml`, `/admin/fiscal/listar`, `/admin/fiscal/conferir` | POST | fiscal-ia | XML/NF-e | Precisa testar | |
| **Upload doc admin** | `/admin/upload-documento-cliente` | POST FormData | **NÃO EXISTE** | `entregas_master`, `inbox_documentos`, etc. | **Ausente no backend** | Já documentado em `PROMPT_N8N_UPLOAD_DOCUMENTO_CLIENTE.md` |

---

## 5. Matriz Frontend × Backend (inconsistências)

| Inconsistência | Frontend | Backend esperado | Severidade |
|---|---|---|---|
| Upload de documento admin não existe no n8n | `/admin/upload-documento-cliente` | criar workflow | 🔴 Crítica |
| Dashboard admin chama `-v2` mas contexto cita `-v1` ativo | `/admin-dashboard-v2` | confirmar v2 ativo, desativar v1 | 🔴 Alta |
| Impostos admin sem `-v2` | `/admin/impostos` | padronizar para `/admin/impostos-v2` | 🟠 Média |
| Equipe duplicada | `/admin/funcionarios` (hook legado) e `/admin/equipe-v2` (página) | unificar para `-v2` | 🟠 Média |
| Agenda v1 e v2 conviventes | ambos chamados | confirmar v2 substituiu v1 | 🟠 Média |
| Central Op. com versões misturadas | create-v5, update-v1, delete-v3, kanban-v3 | consolidar para v3+ | 🟠 Média |
| Rotas `/admin/entregas`, `/admin/tarefas`, `/admin/agenda` redirecionam mas hooks ainda existem | App.tsx | revisar componentes órfãos | 🟡 Baixa |
| `/dashboard`, `/biblioteca`, `/chamados`, `/honorarios`, `/impostos` sem guard de sessão cliente | App.tsx | criar `ClientRouteGuard` | 🔴 Alta |
| `N8N_BASE` hardcoded | AdminAuthContext.tsx | mover para `.env` (`VITE_N8N_BASE`) | 🟡 Baixa |
| Hooks chamando endpoints v1 antigos (`admin-clientes-options-v1`) | useOptionsAPI | confirmar ainda ativos | 🟡 Baixa |

---

## 6. Mapa do Banco de Dados (com base no código + contexto)

| Tabela | Finalidade | Módulos consumidores | Campos confirmados no código | Risco |
|---|---|---|---|---|
| `clientes` | Cadastro de clientes | Login portal, listagens admin, permissões, drive | `id`, `nome_cliente`, `email`, `whatsapp`, `drive_folder_id` (citado) | Confirmar coluna `id_pasta_raiz` vs `drive_folder_id` |
| `clientes_emails_autorizados` | Multi-login por CNPJ | Login cliente | não confirmado no projeto atual | Validar schema |
| `funcionarios` | Equipe interna | Login admin, equipe, permissões | `id`, `nome`, `cargo`, `email` | OK |
| `security_sessoes_clientes` | Sessão cliente | Login cliente | `token`, `expira_em` | OK |
| `security_sessoes_funcionarios` | Sessão admin | Login admin | `token`, `admin_id`, `expira_em` | OK |
| `log_tentativas_login` | Rate-limit | Login | não confirmado | Validar |
| `permissoes_funcionario_modulos` | RBAC por módulo | PermissoesManager | `funcionario_id`, `modulo`, `pode_ver/editar` (citado) | Confirmar nomes |
| `permissoes_funcionario_clientes` | Acesso por cliente | PermissoesManager | idem | Confirmar |
| `impostos_obrigacoes` | Guias/obrigações | Impostos, Agenda, Dashboard | `cliente_id`, `titulo`, `competencia`, `vencimento`, `status`, `valor`, `area`, `arquivo_url` | OK |
| `catalogo_obrigacoes` | Catálogo padrão | Geração de obrigações | não confirmado | Validar |
| `tickets_master` | Chamados | Tickets cliente/admin, Central Op. | `id`, `cliente_id`, `assunto`, `status`, `criado_em` | OK |
| `tasks_master` | Tarefas internas | Central Op. | similar tickets | OK |
| `entregas_master` | Entregas mensais | Central Op., biblioteca | `id`, `cliente_id`, `titulo`, `area`, `competencia`, `arquivo_url` | **Risco:** módulo removido do menu |
| `inbox_documentos` | Documentos enviados pelo cliente | AdminDocumentos | `id`, `cliente_id`, `nome`, `url` | OK |
| `honorarios_contratos` | Contratos vigentes | Honorários | `cliente_id`, `valor_mensal`, `dia_vencimento`, `status` | OK |
| `honorarios_parcelas` | Mensalidades | Honorários + CRON | `contrato_id`, `competencia`, `vencimento`, `status` | OK |
| `honorarios_servicos_avulsos` | Cobranças extras | Honorários | não confirmado em detalhe | Validar |
| `honorarios_recibos_sequencia` | Numeração de recibos | Honorários | não confirmado em detalhe | Validar |
| `logs_auditoria` | Trilha de auditoria | n8n geral | não confirmado | Confirmar uso real |
| `admin_sessoes` / `admin_funcionarios` | Citado no prompt do upload | upload-doc | divergente de `security_sessoes_funcionarios` | **Padronizar nomenclatura** |

---

## 7. Fluxos Operacionais

### A) Cadastro de cliente
1. Admin abre `/admin/clientes` → modal de novo cliente.
2. Front envia POST `/admin/novo-cliente-v2`.
3. n8n: insere em `clientes`; insere em `clientes_emails_autorizados`; cria pasta raiz Drive; cria subpastas `00_INBOX..99_DIVERSOS`; grava `drive_folder_id`; envia e-mail de boas-vindas.
4. Retorna `{ success, cliente_id }` → front atualiza lista.

### B) Login cliente
1. `/login` → POST `/portal-serdial-v2 { email, senha }`.
2. n8n valida (hash bcrypt) + rate-limit em `log_tentativas_login`.
3. Gera token, grava em `security_sessoes_clientes`.
4. Front grava `auth_token` + `client_user` no localStorage → redireciona para `/dashboard`.

### C) Login administrativo
1. `/admin/login` → POST `/admin/login-v2`.
2. n8n valida funcionário ativo + sessão.
3. Retorna `{ success, token, user:{id,nome,cargo} }`.
4. Front grava `admin_auth_token` + `admin_user` → `/admin`.

### D) Lançamento de imposto
1. Admin em `/admin/impostos` cria guia (form + arquivo).
2. POST `/admin/impostos` (ou `/admin/novo-imposto`) FormData.
3. n8n identifica cliente, upload no Drive (`01_FISCAL` ou `02_PESSOAL`), grava em `impostos_obrigacoes`.
4. Cliente vê em `/impostos` via `/portal/impostos-v2` e na agenda.

### E) Agenda
- `/admin` (Central Op.) chama `/admin-dashboard-v2` (ou agenda-v2) que consolida `impostos_obrigacoes + tasks_master + tickets_master + entregas_master`.
- Cálculo de prazo no SQL (`CASE WHEN vencimento < CURDATE() ...`).
- Front exibe por status: atrasado / vence hoje / próximo / futuro / concluído.

### F) Central operacional
- Hub único em `/admin`.
- CRUD via `/admin-create-item-v5`, `/admin-update-item-v1`, `/admin-delete-item-v3`, listagem `/admin-kanban-v3`.
- Tipos: `task`, `ticket`, `obrigacao`, `entrega`.

### G) Honorários
1. Admin cadastra contrato em `/admin/honorarios` → `/admin/honorarios-v2`.
2. CRON mensal gera parcelas em `honorarios_parcelas`.
3. CRON diário marca atrasos.
4. CRON semanal envia lembretes (SMTP + WhatsApp).
5. Cliente acessa `/honorarios` → `/portal/honorarios-v2`.
6. Admin registra pagamento → atualiza parcela + gera recibo (sequência em `honorarios_recibos_sequencia`).

---

## 8. Diagnóstico de Riscos

| # | Risco | Severidade | Onde |
|---|---|---|---|
| 1 | Webhook de upload admin→cliente ausente | 🔴 Crítica | n8n |
| 2 | Rotas cliente sem guard de sessão | 🔴 Alta | App.tsx |
| 3 | Mix de versões v1/v2/v3/v5 em endpoints similares | 🔴 Alta | hooks + n8n |
| 4 | Permissões vazias podem causar tela branca | 🔴 Alta | usePermissoes / AdminRouteGuard |
| 5 | `responseMode: lastNode` em produção (citado no contexto) | 🟠 Média | n8n (verificar) |
| 6 | CORS / preflight OPTIONS não auditado em todos workflows | 🟠 Média | n8n |
| 7 | SQL montado por string (INSERT dinâmico no upload-doc proposto) | 🟠 Média | n8n (futuro) |
| 8 | Status divergente entre módulos (`pendente`/`a_fazer`/`pago`/`concluido`) | 🟠 Média | tasks/tickets/obrigações |
| 9 | URLs hardcoded (`N8N_BASE`) | 🟡 Baixa | AdminAuthContext.tsx |
| 10 | Hooks legados ainda no bundle (`/admin/funcionarios`, agenda-v1) | 🟡 Baixa | useFuncionarios, useAgenda |
| 11 | Falta de tratamento amigável de erro 5xx em vários hooks | 🟠 Média | hooks/* |
| 12 | Logs de auditoria não confirmados | 🟠 Média | n8n + `logs_auditoria` |
| 13 | Tokens sem endpoint explícito de revogação (logout só limpa localStorage) | 🟠 Média | n8n |
| 14 | Sem testes E2E nem unitários relevantes (`example.test.ts` apenas) | 🟡 Baixa | repo |
| 15 | Divergência `admin_sessoes` (doc) vs `security_sessoes_funcionarios` (contexto) | 🟠 Média | docs vs DB |

---

## 9. Backlog Priorizado

### P0 — Crítico
| ID | Item | Módulo | Esforço | Risco se não fizer | Arquivos/Endpoints |
|---|---|---|---|---|---|
| P0-1 | Criar webhook `/admin/upload-documento-cliente` no n8n | Documentos | Alto | Form admin inutilizado | `PROMPT_N8N_UPLOAD_DOCUMENTO_CLIENTE.md` |
| P0-2 | Criar `ClientRouteGuard` e proteger rotas `/dashboard`, `/biblioteca`, `/chamados`, `/impostos`, `/honorarios` | Auth cliente | Baixo | Vazamento de dados sem login | `App.tsx`, `ClientAuthContext` |
| P0-3 | Confirmar e ativar `/admin-dashboard-v2`; desativar v1 | Dashboard | Baixo | Dashboard quebrado | `useAdminDashboard.ts` |
| P0-4 | Hardening de `usePermissoes` para nunca devolver `undefined` (defaults seguros) | Permissões | Baixo | Tela branca admin | `usePermissoes.ts`, `AdminRouteGuard.tsx` |

### P1 — Necessário
| ID | Item | Módulo | Esforço | Risco | Arquivos |
|---|---|---|---|---|---|
| P1-1 | Padronizar Impostos para `/admin/impostos-v2` + `/admin/novo-imposto-v2` | Impostos | Médio | Inconsistência | `useImpostos.ts`, n8n |
| P1-2 | Unificar equipe em `/admin/equipe-v2` (remover `/admin/funcionarios`) | Equipe | Baixo | Duplicidade | `useFuncionarios.ts` |
| P1-3 | Consolidar Central Operações em v3 único (`create/update/delete/kanban`) | Central Op. | Médio | Bugs CRUD | `useTasks.ts`, n8n |
| P1-4 | Auditoria CORS+OPTIONS em todos workflows; trocar `lastNode` por `Respond to Webhook` | n8n | Médio | CORS/timeout | n8n |
| P1-5 | Padronizar enum de status (a_fazer, em_andamento, aguardando_cliente, em_conferencia, concluido, atrasado) | Cross | Médio | Filtros quebrados | hooks + n8n |
| P1-6 | Mover `N8N_BASE` e flags para `.env` (`VITE_N8N_BASE`) | Infra | Baixo | Dificuldade deploy | AdminAuthContext |
| P1-7 | Tratamento padrão de erro + toast nos hooks | UX | Médio | UX ruim | hooks/* |
| P1-8 | Endpoint de logout que invalida token em `security_sessoes_*` | Auth | Baixo | Sessão zumbi | n8n |

### P2 — Melhorias
| ID | Item |
|---|---|
| P2-1 | Histórico de envios na tela "Enviar ao Cliente" |
| P2-2 | Notificações push/in-app via Realtime |
| P2-3 | Filtros avançados e exportação CSV/PDF padrão |
| P2-4 | Métricas de SLA em tickets |
| P2-5 | Internacionalização de mensagens de erro |
| P2-6 | Logs estruturados (JSON) no n8n |

### P3 — Evoluções
| ID | Item |
|---|---|
| P3-1 | App mobile (PWA) do portal cliente |
| P3-2 | OCR automático de documentos enviados |
| P3-3 | Integração Receita Federal / e-CAC |
| P3-4 | BI/Analytics interno |

---

## 10. Plano de Execução por Etapas

### Fase 1 — Auditoria do frontend e endpoints
- **Objetivo:** validar tabela Tela×Endpoint deste dossiê acessando cada tela em preview e capturando o status real.
- **Arquivos:** `App.tsx`, `hooks/*`, `pages/*`.
- **Teste:** abrir cada rota logado e verificar `Network` → status 2xx.
- **Aceite:** lista de endpoints reais confirmada vs documentada.

### Fase 2 — Autenticação e permissões
- Implementar `ClientRouteGuard`; hardening `usePermissoes`.
- Aceite: nenhuma rota cliente acessível sem token; admin sem permissão nunca vê tela branca.

### Fase 3 — Padronização de APIs e CORS
- Mover `N8N_BASE` para `.env`; revisar todos workflows com OPTIONS e `Respond to Webhook`; padronizar versionamento.
- Aceite: 100% dos endpoints com preflight OK e versão única.

### Fase 4 — Clientes, funcionários e documentos
- P0-1 (upload admin) + P1-2 (equipe) + revisar `/admin/novo-cliente-v2` end-to-end.
- Aceite: criar cliente, equipe e enviar documento sem erros.

### Fase 5 — Impostos e agenda
- P1-1 + confirmação v2 da agenda + dashboard.
- Aceite: lançar guia → aparece para cliente e na agenda admin.

### Fase 6 — Tickets, tarefas e Central de Operações
- P1-3 + padronização de status.
- Aceite: criar/mover/encerrar item no Kanban sem erro; filtros estáveis.

### Fase 7 — Honorários
- Verificar CRONs ativos; testar geração de parcelas e recibo.
- Aceite: fluxo completo contrato → parcela → pagamento → recibo.

### Fase 8 — Testes gerais
- Executar checklist da seção 11.
- Aceite: 100% verde em ambiente de homologação.

### Fase 9 — Documentação e publicação
- Atualizar README, gerar changelog, publicar.
- Aceite: domínio principal servindo versão estável.

---

## 11. Checklist de Testes

**Login cliente**
- [ ] Login válido devolve token e redireciona
- [ ] Senha inválida → mensagem clara
- [ ] E-mail inexistente → mensagem genérica (não vazar)
- [ ] Bloqueio após N tentativas (rate limit)
- [ ] Token expirado → redireciona `/login`

**Login admin**
- [ ] Admin válido acessa `/admin`
- [ ] Operador acessa apenas módulos permitidos
- [ ] Funcionário inativo é rejeitado
- [ ] Token inválido cai em `/admin/login`
- [ ] Permissões vazias não causam tela branca

**Clientes**
- [ ] Criar cliente novo
- [ ] Duplicidade de e-mail rejeitada
- [ ] Pastas Drive criadas (`00_INBOX..99_DIVERSOS`)
- [ ] `id_pasta_raiz` gravado no banco
- [ ] E-mail de boas-vindas enviado

**Impostos**
- [ ] Lançar guia fiscal (área 01_FISCAL)
- [ ] Lançar guia pessoal (área 02_PESSOAL)
- [ ] Cliente visualiza no portal
- [ ] Alterar status (pendente→pago)
- [ ] Aparece na agenda com cor correta

**Honorários**
- [ ] Criar contrato
- [ ] Gerar parcelas (manual + CRON)
- [ ] Marcar atraso (CRON diário)
- [ ] Registrar pagamento + recibo
- [ ] Portal mostra histórico correto

**Central operacional**
- [ ] Criar tarefa
- [ ] Criar ticket
- [ ] Criar obrigação
- [ ] Mover entre colunas (drag-and-drop)
- [ ] Filtros por cliente/responsável/data

**Documentos**
- [ ] Upload admin → cliente (depende P0-1)
- [ ] Cliente envia documento (inbox)
- [ ] Detalhe / complementar documento
- [ ] Download via Drive abre sem erro

---

## 12. Dúvidas Técnicas Pendentes

1. Qual é o nome **canônico** da tabela de sessão admin: `admin_sessoes` (doc upload) ou `security_sessoes_funcionarios` (contexto)?
2. `clientes.drive_folder_id` ou `clientes.id_pasta_raiz`?
3. `/admin-dashboard-v1` está ativo, inativo ou foi removido?
4. Existe workflow ativo para `/admin/funcionarios` ou pode ser removido do frontend?
5. Endpoints `agenda-v1` x `agenda-v2`: qual o consumo real?
6. Enum oficial de status para tarefas/tickets/obrigações já existe documentado?
7. Estratégia de logout no backend (invalidação de token) está implementada?
8. CRONs de honorários estão **ativos** atualmente?
9. Z-API/Evolution já está conectado em produção (WhatsApp)?
10. SMTP Hostinger atende volume previsto?

---

## 13. Recomendação Final

**Sequência sugerida (sem alterar código nesta etapa):**

1. **Validar este dossiê** com a equipe (responder às 10 dúvidas acima).
2. Aprovar **Fase 1 (auditoria assistida)** — eu rodo as telas em preview e marco cada endpoint como OK/Erro.
3. Atacar o backlog **P0** na ordem 1→4, uma alteração por vez, com explicação prévia.
4. Avançar para P1 conforme fases 3–7.

> Nenhuma alteração de código foi feita nesta resposta, conforme regra final do briefing.

