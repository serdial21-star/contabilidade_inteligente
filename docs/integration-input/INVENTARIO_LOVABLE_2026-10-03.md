# Inventário do site Serdial21 (somente leitura) — T-0006

Fonte: resposta do Lovable ao prompt `PROMPT_INVENTARIO_LOVABLE_2026-10-03.md`,
repassada pelo usuário em 03/10/2026 e transcrita sem alteração de conteúdo.
O Lovable declarou não ter alterado nem publicado nada e omitiu segredos e o
e-mail fixo encontrado no código. Afirmações não verificadas pelo Claude, exceto
onde a T-0006 registra o cruzamento com a exportação do n8n.

---

Data da leitura: 03/10/2026. Nenhum arquivo do projeto foi alterado, nada foi publicado.
Base n8n usada em todo o código: `https://n8n.serdial21.com/webhook` (abaixo só o path).
"proxy" = edge function `proxy-webhook` (chamada via `supabase.functions.invoke` ou fetch direto).

## 1. Páginas e rotas (src/App.tsx)

| Rota | Componente | Área | Guarda | Permissão verificada |
|---|---|---|---|---|
| `/` | redireciona `/login` | pública | — | — |
| `/login` | Login | pública | — | — |
| `/esqueci-senha`, `/redefinir-senha` | EsqueciSenha, RedefinirSenha | pública | — | — |
| `/meus-documentos` | redireciona `/biblioteca` | — | — | — |
| `/loguin` → `/login`, `/admin/loguin` → `/admin/login` | redirecionamentos | pública | — | — |
| `/dashboard`, `/chamados`, `/documentos`, `/biblioteca`, `/honorarios`, `/impostos` | Dashboard, Chamados, EnviarDocumentos, Biblioteca, Honorarios, Impostos | portal do cliente | `ClientRouteGuard` (rota-layout): sem `client_user`+`auth_token` → `/login`; com eles chama `/portal/me-v2` pelo proxy; erro ou `success≠true` → logout local + `/login` | nenhuma permissão por módulo na rota. `useClientPermissoes` só filtra itens do menu (AppSidebar) |
| `/admin/login`, `/admin/esqueci-senha`, `/admin/redefinir-senha` | AdminLogin, AdminEsqueciSenha, AdminRedefinirSenha | pública | — | — |
| `/admin` | AdminDashboard | painel | `AdminRouteGuard` | `dashboard`/`visualizar`. Sem permissão → tela "Acesso restrito" |
| `/admin/clientes` | AdminClientes | painel | `AdminRouteGuard` | `clientes` (+ `useCanAccess` dentro da página) |
| `/admin/tickets` | AdminTickets | painel | `AdminRouteGuard` | `tickets` |
| `/admin/documentos` | AdminDocumentos | painel | `AdminRouteGuard` | `documentos` |
| `/admin/upload-documentos` | AdminUploadDocumentos | painel | `AdminRouteGuard` | `documentos` |
| `/admin/equipe` | AdminEquipe | painel | `AdminRouteGuard` + `ProtectedRoute` | `equipe` + cargo Administrador/Admin (`useCanAccess`) |
| `/admin/configuracoes` | AdminConfiguracoes | painel | `AdminRouteGuard` + `ProtectedRoute` | `configuracoes` + cargo Administrador/Admin |
| `/admin/impostos` | AdminImpostos | painel | `AdminRouteGuard` | `impostos` |
| `/admin/honorarios` | AdminHonorarios | painel | `AdminRouteGuard` | `honorarios` |
| `/admin/ferramentas-ia` | AdminFerramentasIA | painel | `AdminRouteGuard` | `ferramentas_ia` |
| `/admin/atalhos` | AdminAtalhos | painel | `AdminRouteGuard` | `atalhos` |
| `/admin/entregas`, `/admin/tarefas`, `/admin/agenda` | redirecionam `/admin` | — | — | — |
| `*` | NotFound | pública | — | — |

Funcionamento do `AdminRouteGuard`: sem `admin_user` → `/admin/login`. Cargo `administrador`/`admin` sempre passa. Os demais precisam de `pode(modulo,'visualizar')` em `usePermissoes` (`/admin/permissoes/funcionario`). Permissão vazia ou resposta sem `success:true` → nega. Sem permissão → `/admin` (ou "Acesso restrito" no próprio `/admin`). `ProtectedRoute` → `/admin`.
Observação: a guarda do painel só olha `admin_user` no navegador. O token é validado apenas quando uma chamada é feita.

## 2. Chamadas externas

Legenda do token: **A** = `Authorization: Bearer admin_auth_token`; **C** = `Authorization: Bearer auth_token`; **X** = token no cabeçalho `x-app-token` (o Authorization leva a chave pública do Supabase); **anon** = só a chave pública do Supabase.

| Arquivo / função | Funcionalidade | Destino | Método | Token | Campos de identificação | Via |
|---|---|---|---|---|---|---|
| AdminAuthContext.login | login do painel | `admin/login-v2` | POST | nenhum (email, senha) | — | n8n direto |
| AdminAuthContext.logout | Sair (painel) | `admin/logout-v1` | POST | A | — | n8n direto |
| AdminAuthContext.adminFetch (genérico) | ver linhas "adminFetch" | n8n `path` | POST/GET | A | — | n8n direto |
| ClientAuthContext.logout | Sair (portal) | `/cliente/logout-v1` | POST | C | — | proxy (fetch direto à função) |
| Login.tsx | login do portal | `/portal-serdial-v2` | POST | nenhum (email, senha) | resposta: id/cliente_id/id_cliente | proxy |
| EsqueciSenha.tsx | pedir nova senha (cliente) | `/portal/solicitar-senha` | POST | nenhum | email | proxy |
| RedefinirSenha.tsx | nova senha (cliente) | `/portal/redefinir-senha` | POST | nenhum (token de redefinição no corpo) | — | proxy |
| AdminEsqueciSenha.tsx | pedir nova senha (painel) | `/admin/solicitar-senha` | POST | nenhum | email | proxy |
| AdminRedefinirSenha.tsx | nova senha (painel) | `/admin/redefinir-senha` | POST | nenhum (token de redefinição no corpo) | — | proxy |
| ClientRouteGuard / Dashboard | sessão do cliente | `/portal/me-v2` | POST | C | — | proxy (portalFetch) |
| useImpostosPortal (Dashboard, Impostos) | impostos do cliente | `/portal/impostos-v2` | POST | C | — | proxy |
| Impostos.tsx | enviar comprovante | `portal/pagar-imposto-v2` | POST multipart | C | imposto_id | n8n direto |
| Chamados.tsx, TicketHistory.tsx | lista de chamados | `/portal/meus-chamados-v2` | POST | C | — | proxy |
| TicketDetailDrawer (cliente) | detalhe e complemento | `/portal/detalhe-chamado`, `/portal/complementar-chamado` | POST | C | ticket id | proxy |
| HelpdeskTicketForm | abrir chamado | `portal/abrir-ticket-v2` (base pode vir de `VITE_N8N_WEBHOOK_URL`) | POST multipart | C | email (cai para um e-mail fixo se não houver usuário) | n8n direto |
| Biblioteca, EnviarDocumentos, MeusDocumentos | documentos do cliente | `/portal/meus-documentos-v2` | POST | C | — | proxy |
| DocumentDetailDrawer | detalhe e complemento | `/portal/detalhe-documento`, `/portal/complementar-documento` | POST | C | documento_id | proxy |
| CertidoesTab / LivrosContabeisTab / ObrigacoesTab | abas da Biblioteca | `/portal/certidoes-v2`, `/portal/livros-contabeis-v2`, `/portal/obrigacoes-v2` | POST | C (portalFetch: não confirmado linha a linha) | — | proxy |
| Biblioteca.tsx (handleBuscarBiblioteca, "legado") | busca por área | `listar-arquivos?email=…&area=…` | GET | **nenhum token**; e-mail fixo na query | email | n8n direto |
| DocumentUploadForm | enviar documentos (cliente) | `portal/receber-arquivo-v2` (base pode vir de `VITE_N8N_WEBHOOK_URL`) | POST multipart | C | — | n8n direto |
| Honorarios.tsx | honorários do cliente | `/portal/honorarios-v2` | POST | C | — | proxy |
| useClientPermissoes | menu do cliente | `/permissoes/cliente` | POST | C | cliente_id | proxy |
| MeusDocumentos (botão Abrir) | baixar arquivo | função `proxy-document-download` → `/security/download-documento` | POST | X (`auth_token`) | tabela, id | edge function |
| useAdminDashboard | dashboard | `/admin-dashboard-v2` | GET | A | — | proxy |
| useOptionsAPI | listas de clientes/funcionários | `/admin-clientes-options-v1`, `/admin-funcionarios-options-v1` | GET | A | — | proxy |
| useListas | opções dinâmicas | `/admin/listas…` | variável (`_method`) | A | — | proxy |
| useImpostos (admin) | impostos | `/admin/impostos` | POST | A | cliente_id (no payload) | proxy |
| useTasks.n8nCall | Central de Operações / kanban | `admin-kanban-v3`, `admin-create-item-v5`, `admin-update-item-v5`, `admin-delete-item-v3` | GET/POST | A | cliente_id, responsavel_id | n8n direto |
| useAgenda | agenda | `admin-agenda-v2` | GET | A | — | n8n direto |
| useClientes | lista de clientes | `admin/clientes-v2` | GET | A | — | n8n direto |
| AdminClientes (criar) | novo cliente | `admin/novo-cliente-v2` | POST multipart | A | funcionario_id | n8n direto |
| AdminClientes (editar) | editar cliente | `/admin/editar-cliente-v2` | POST multipart | A | cliente_id, funcionario_id | adminFetch |
| ClientLogoUpload | logo do cliente | função `client-logo` (bucket `client-logos`) | POST multipart | A | clientId | edge function |
| AdminTickets | tickets | `/admin/tickets-v2` (GET), `/admin/responder-ticket-v2` | GET/POST | A | ticket_id | adminFetch |
| AdminDocumentos | caixa de documentos | `/admin/documentos-v2` (GET); upload em `admin/upload-documento-cliente` | GET/POST multipart | A | cliente_id (FormData) | adminFetch / n8n direto |
| AdminUploadDocumentosForm | enviar ao cliente | `/admin/upload-documento-cliente` | POST multipart | A | cliente_id dentro de `metadata` | adminFetch |
| AdminImpostos | criar / editar imposto | `admin/novo-imposto`, `admin/impostos-v2` | POST multipart | A | cliente_id (criar), id (editar) | n8n direto |
| AdminHonorarios | contratos e parcelas | `/admin/honorarios-v2`, `/admin/honorarios-parcelas-v2` | POST | A | cliente_id (não confirmado o nome exato) | adminFetch |
| AdminEquipe, PermissoesManager | equipe | `/admin/equipe-v2` | POST | A | — | adminFetch |
| FuncionarioFormDialog | criar / editar funcionário | `/admin/novo-funcionario`, `/admin/editar-funcionario` | POST | A | id do funcionário | adminFetch |
| useFuncionarios (TaskCreateModal) | funcionários ativos | `/admin/funcionarios` | POST | A | — | adminFetch |
| usePermissoes, PermissoesManager | permissões | `/admin/permissoes/funcionario`, `/admin/permissoes/cliente`, `…/salvar`, `/admin/clientes-v2` | POST/GET | A | funcionario_id, cliente_id | adminFetch |
| useAtalhos | atalhos | `/admin/atalhos` | POST | A | — | adminFetch |
| AdminFiscal (Inteligência Fiscal) | painel fiscal | `/admin/fiscal/listar`, `/admin/fiscal/upload-xml`, `/admin/fiscal/conferir` | POST | A | cliente_id (não confirmado) | adminFetch |
| AdminFerramentasIA.executeExtraction | Extrator Fiscal XML | `admin/upload-xml` | POST multipart | A | cliente_id, tipo_operacao | n8n direto |
| ApuracaoICMSView | Apuração ICMS/CMV | função `proxy-file-upload` → `/ferramentas-ia/apuracao-icms` | POST multipart | X (`admin_auth_token`) | — | edge function |
| AdminFerramentasIA.callAI | Analista de Balanço | função `ai-analyst` | POST | **anon** (nenhum token do Serdial21) | — | edge function |
| AdminSidebar.abrirSistemaB | Contabilidade Inteligente | função `sistema-b-bridge-token` | POST | X (`admin_auth_token`) | — | edge function |

Endpoints pedidos explicitamente:
- `admin/upload-xml`: AdminFerramentasIA (acima). Também existe `admin/fiscal/upload-xml` (AdminFiscal).
- `ferramentas-ia/apuracao-icms`: via `proxy-file-upload` (acima).
- `admin/integracao-cnd-v1`: **não encontrada no código**.
- `admin/tasks`: **não encontrada no código**.
- `admin-motor-obrigacoes-v1`: **não encontrada no código**.
- `portal/honorarios-v2`: Honorarios.tsx (sem `-v2`: não encontrada).
- `portal/meus-documentos`: só a `-v2` (sem sufixo: não encontrada).
- `portal/meus-chamados`: só a `-v2` (sem sufixo: não encontrada).
- `admin/novo-cliente`: só a `-v2` (sem sufixo: não encontrada).
- `portal/receber-arquivo`: só a `-v2` (sem sufixo: não encontrada).

## 3. Ferramentas IA (AdminFerramentasIA)

| Card | O que faz | Chamadas | Login | Token enviado | IA |
|---|---|---|---|---|---|
| Analista de Balanço IA | envia balanço (texto ou base64) e recebe análise em streaming | `ai-analyst` | precisa entrar na tela do painel; a função não exige token do Serdial21 | só a chave pública | sim: Lovable AI Gateway, modelo `google/gemini-2.5-flash`, pela edge function |
| Extrator Fiscal XML (NF-e) | envia XMLs e recebe as notas extraídas | `admin/upload-xml` (n8n direto) | sim | A | IA não confirmada (o processamento fica no n8n) |
| Apuração de ICMS e CMV | envia planilha e recebe link do Google Sheets | `proxy-file-upload` → `/ferramentas-ia/apuracao-icms` | sim | X | não confirmado (fica no n8n) |
| Inteligência Fiscal | painel ICMS/PIS/COFINS (AdminFiscal em modo embutido) | `/admin/fiscal/*` | sim | A | não confirmado |

## 4. Edge functions (supabase/functions + config.toml)

| Função | O que faz | verify_jwt | Valida token do Serdial21? | Destinos | Lista de paths permitidos | Variáveis de ambiente | Repassa Authorization |
|---|---|---|---|---|---|---|---|
| proxy-webhook | repassa qualquer `path` ao n8n (método via `_method`) | **false** | não, só repassa | `n8n…/webhook{path}` (qualquer path) | **nenhuma** (aceita qualquer path) | nenhuma | sim, o cabeçalho recebido |
| proxy-file-upload | repassa upload multipart | true | não, só repassa (x-app-token → Authorization) | n8n | `["/ferramentas-ia/apuracao-icms"]` | não confirmado além das padrão | repassa x-app-token como Bearer (fallback Authorization) |
| proxy-document-download | baixa arquivo e devolve o binário | true | não, só repassa | n8n | `["/security/download-documento"]` | não confirmado além das padrão | idem (x-app-token) |
| ai-analyst | chat de análise financeira | true | **não** (aceita a chave pública) | Lovable AI Gateway | — | `LOVABLE_API_KEY` | não |
| client-logo | envia/remove logo no bucket | false | sim: consulta `admin/permissoes/funcionario` com o Bearer e exige `success:true`; senão 401 | n8n + Storage | — | `SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY` | sim, para o n8n |
| sistema-b-bridge-token | gera token RS256 para o Sistema B | true | sim: `security/validar-sessao-funcionario` | n8n | — | `SISTEMA_B_BRIDGE_PRIVATE_KEY_PEM` | sim (x-app-token como Bearer) |
| sistema-b-jwks | publica a chave pública | false | — | — | — | `SISTEMA_B_BRIDGE_PUBLIC_JWK` | não |

Observação: o resumo anterior desta conversa dizia que `proxy-webhook` estava com `verify_jwt = true`. No `config.toml` atual está **false**, e o código não tem lista de paths permitidos.

## 5. Supabase: tabelas e armazenamento
- Tabelas do banco do Supabase: nenhuma usada pelo site (não há `supabase.from(...)` no frontend; os dados ficam no MySQL via n8n).
- Bucket `client-logos`: **público** (migration de 04/03/2026). Políticas da migration: leitura pública; inserir, atualizar e apagar por "authenticated". Quem envia: função `client-logo` (service role). Quem lê: qualquer pessoa, pela URL pública. Se as políticas foram mudadas depois fora de migrations: não confirmado.

## 6. Autenticação e sessão no navegador
- localStorage: `admin_auth_token`, `admin_user` (painel); `auth_token`, `client_user` (portal); `theme`.
- sessionStorage: `admin_permissoes`, `client_permissoes` (cache das permissões).
- Login do painel: `admin/login-v2` → grava token e usuário. Sair: limpa na hora, revoga em `admin/logout-v1` (5 s), vai para `/admin/login`.
- Login do portal: `/portal-serdial-v2` pelo proxy → grava `auth_token`/`client_user`. Sair: limpa na hora, revoga em `/cliente/logout-v1` pelo proxy (5 s), vai para `/login`.
- 401 no painel: `adminFetch` limpa o usuário e vai para `/admin/login` (também quando a mensagem contém "sessão expirada"). useTasks, AdminDocumentos e Ferramentas IA tratam 401 por conta própria (Ferramentas IA também trata 403). useAdminDashboard redireciona quando recebe erro de sessão.
- 401 no portal: Chamados e Biblioteca verificam "401/unauthorized" na mensagem. ClientRouteGuard faz logout se `/portal/me-v2` falhar. Tratamento uniforme de 403: não confirmado.

## 7. Itens sem uso ou duplicados
- Páginas importadas no App.tsx cujas rotas só redirecionam: `AdminEntregas`, `AdminTarefas`, `AdminAgenda`, `MeusDocumentos` (MeusDocumentos ainda tem o botão de download, mas a rota leva para Biblioteca).
- `src/pages/Index.tsx`: não referenciada.
- `TicketHistory.tsx`: não referenciado.
- `TaskKanbanBoard`, `TaskFiltersBar` e `TaskCreateModal` só são usados em AdminTarefas, que hoje não abre. Por isso `useFuncionarios` (`/admin/funcionarios`) fica sem uso prático e repete `/admin/equipe-v2` e `/admin-funcionarios-options-v1`.
- `mockData` ainda é usado em Dashboard e NotificationCenter.
- Duplicados: clientes (`admin/clientes-v2` em useClientes e PermissoesManager, e `/admin-clientes-options-v1`); impostos (`/admin/impostos` pelo proxy, `admin/impostos-v2` e `admin/novo-imposto` direto); upload de documento do admin em dois lugares (AdminDocumentos e AdminUploadDocumentosForm); upload de XML (`admin/upload-xml` e `admin/fiscal/upload-xml`).
- Biblioteca "legado" (`listar-arquivos`) sem token e com e-mail fixo.

## Pontos não confirmados
- Se o n8n valida de fato o Bearer em cada webhook chamado direto ou pelo proxy (fica fora do código do site).
- Se as três abas da Biblioteca usam portalFetch em todas as chamadas (não li linha a linha).
- Nomes exatos dos campos de cliente em AdminHonorarios e AdminFiscal.
- Se as ferramentas Extrator, ICMS e Inteligência Fiscal usam IA dentro do n8n.
- Estado atual das políticas do bucket `client-logos` no servidor (só li a migration).
- Se `VITE_N8N_WEBHOOK_URL` está definida em produção (muda o destino de abrir chamado e enviar documento).
- Se o `verify_jwt=false` do proxy-webhook é o que está publicado hoje.
