# T-0006 — Webhooks ativos sem autenticação e sessão revogada aceita (inventário do n8n)

| Campo | Valor |
|---|---|
| Estado | DIAGNÓSTICO — aguardando decisões do usuário |
| Origem | QUADRO, fila item 19 (SG-10); inventário de 03/10/2026 |
| Sistema | Sistema A (n8n) |
| Exige ADR | não, para a contenção; a decisão de manter ou proteger cada endpoint é do usuário |
| Exige ação do usuário | sim — desativar/proteger workflows no n8n; rotacionar duas credenciais |

---

## 1. Diagnóstico (Claude)

### [2026-10-03] Claude — Inventário

**Fonte.** `n8n export:workflow --all --separate` executado pelo usuário no container `n8n-n8n-1` (n8n 2.6.4): 149 workflows, 60 ativos. Cópia mantida só na pasta temporária da sessão do Claude, fora do repositório; o usuário apagou a cópia da VPS. A exportação não inclui credenciais. Classificação por leitura dos nós (consultas SQL, código e webhooks); não houve chamada a nenhum endpoint.

**A. Ativos que validam sessão com `revogado_em IS NULL`:** 39 workflows administrativos e do portal, inclusive `admin/permissoes/cliente` (o SG-10 citava esse caso; já foi corrigido). Todos usam `NOW()` para expiração (o MySQL de produção roda em UTC, conforme a T-0005). Os de procedure (T-0003, T-0005, recuperação de senha) validam dentro do banco.

**B. Ativo que valida sessão sem `revogado_em` (SG-10 remanescente):**
- `[WEBHOOK] POST /portal/honorarios-v2 (Corrigido)` — nó "SQL validar token" aceita sessão de cliente revogada até expirar.

**C. Ativos expostos sem nenhuma autenticação** (webhook sem `authentication`, sem consulta de sessão, sem chamada a validador):

| Endpoint | Workflow | Efeito para qualquer pessoa na internet | Observação |
|---|---|---|---|
| `POST portal/meus-documentos` | API - Portal - Meus Documentos - Serdial21 | lê os documentos de qualquer cliente informando `cliente_id` | SQL por interpolação; o frontend usa `-v2` (dossiê) |
| `POST portal/meus-chamados` | API - Portal - Meus Chamados - Serdial21 | lê os chamados de qualquer cliente | idem |
| `POST admin/novo-cliente` | [CRUD] Cadastro de Novo Cliente (Admin) - V8 Final | cria cliente, e-mail autorizado e pastas no Drive | contorna a T-0003; SQL por interpolação; CORS `*`; o frontend usa `-v2` |
| `POST portal/receber-arquivo` | [CRUD] Receber Arquivo do Portal - V5 | grava arquivo na pasta do Drive de qualquer cliente e registra no inbox | o frontend usa `-v2` |
| `POST admin/upload-xml` | API - Fiscal - Upload XML MultiFile V7 Completo | grava NF-e no banco e no Drive para qualquer `cliente_id` | uso pelo frontend não documentado |
| `POST admin/integracao-cnd-v1` | API - Receber Extração CND (Google Colab) | grava certidões de qualquer CNPJ | SQL por interpolação; chamado pelo Colab |
| `POST admin/tasks` | Serdial21 - Admin Tasks Kanban v1.0 | lista, cria e altera tarefas | SQL por interpolação |
| `GET admin-motor-obrigacoes-v1` | SERD_GERADOR_OBRIGACOES_AUTO_v1 | dispara a geração de obrigações (também roda por cron) | — |
| `POST ferramentas-ia/apuracao-icms` | API Lovable - Apuracao ICMS e CMV v9 | consome Drive/Sheets com arquivo enviado | — |

Os quatro primeiros têm substitutos `-v2` autenticados; o dossiê de 21/09 não registra uso das versões antigas pelo frontend.

**D. Credenciais escritas dentro de nós** (workflows inativos; continuam gravadas no banco do n8n e nas exportações):
- "Automação - Finalizar Ticket": token de acesso da API da Meta (prefixo `EAA`) num cabeçalho `Authorization`.
- "LEGADO - Pericia tentativa monolitica": chave de API do Google (prefixo `AIza`).
Valores não transcritos aqui.

**E. Observados e já na fila:** tokens de login gerados com `Math.random` e SQL interpolado nos dois logins (item 7); CORS `*` em vários workflows.

---

## 2. Decisões do usuário

### [2026-10-03] Usuário
- Contenção: desativar agora os 4 workflows antigos (`portal/meus-documentos`, `portal/meus-chamados`, `admin/novo-cliente` V8, `portal/receber-arquivo` V5).
- Os outros 5 endpoints sem autenticação (`admin/upload-xml`, `admin/integracao-cnd-v1`, `admin/tasks`, `admin-motor-obrigacoes-v1`, `ferramentas-ia/apuracao-icms`) "todos serão utilizados" — precisam ser protegidos, não desativados.
- Credenciais expostas: o usuário não sabe onde ficam; o Claude orienta a localização. Serviços identificados pelos nós: token da WhatsApp Cloud API da Meta (`graph.facebook.com/v22.0/<phone_number_id>/messages`, workflow "Automação - Finalizar Ticket") e chave de API do Google usada no Cloud Vision (`vision.googleapis.com/v1/images:annotate`, workflow "LEGADO - Pericia tentativa monolitica").

### [2026-10-03] Claude — Chamadores identificados e inventário do site

- Tela "Ferramentas IA" do painel (captura do usuário): "Extrator Fiscal XML (NF-e)" → `admin/upload-xml`; "Análise de Apuração de ICMS e CMV" → `ferramentas-ia/apuracao-icms`. "Analista de Balanço IA" e "Inteligência Fiscal" não têm workflow no n8n; provavelmente Lovable/Supabase — autenticação não verificada.
- A pedido do usuário, prompt somente leitura para o Lovable descrever o site inteiro (rotas, todas as chamadas externas e como se autenticam, edge functions, Supabase, sessão): `docs/integration-input/PROMPT_INVENTARIO_LOVABLE_2026-10-03.md`. O resultado define o briefing de proteção dos endpoints.

### [2026-10-03] Usuário
- Os 4 workflows antigos foram desativados.

### [2026-10-03] Claude — Cruzamento com o inventário do Lovable

Inventário do site recebido do Lovable (somente leitura; sem segredos). Cruzado com a exportação do n8n:

1. **Chamados pelo site, sem validação no n8n:** `admin/upload-xml` (painel envia Bearer `admin_auth_token`, o n8n ignora) e `ferramentas-ia/apuracao-icms` (via edge function `proxy-file-upload`, que repassa o token como Bearer; o n8n ignora). Correção no n8n: validar a sessão de funcionário antes de qualquer efeito; o frontend já envia o token.
2. **Não chamados pelo site:** `admin/integracao-cnd-v1` (Google Colab, externo), `admin/tasks` (a tela de tarefas redireciona para `/admin` e usa outros endpoints) e `admin-motor-obrigacoes-v1` (o workflow também roda por cron às 06:05).
3. **Edge functions do Supabase:**
   - `proxy-webhook`: `verify_jwt = false` e **sem lista de paths permitidos** — repassa qualquer path ao n8n. Como os webhooks do n8n já são públicos, a exposição adicional é pequena, mas o proxy serve de relay anônimo e impede restringir o n8n por origem no futuro.
   - `ai-analyst`: aceita apenas a chave pública do Supabase (presente no bundle do site); qualquer pessoa pode consumir o Lovable AI Gateway (`google/gemini-2.5-flash`) — custo e uso indevido. `client-logo` e `sistema-b-bridge-token` já validam a sessão do Serdial21 e servem de modelo.
4. **Frontend:** busca "legado" da Biblioteca chama `listar-arquivos` sem token e com e-mail fixo (o workflow correspondente está inativo no n8n); `HelpdeskTicketForm` usa um e-mail fixo quando não há usuário.
5. **Chamados pelo site e inexistentes no n8n** (funcionalidades quebradas, não falha de segurança): `portal/detalhe-chamado`, `portal/complementar-chamado`, `portal/detalhe-documento`, `portal/complementar-documento`, `portal/certidoes-v2`, `portal/livros-contabeis-v2`, `portal/obrigacoes-v2`, `admin/fiscal/listar`, `admin/fiscal/upload-xml`, `admin/fiscal/conferir` (a "Inteligência Fiscal" depende dos três últimos).
6. Bucket `client-logos` público (leitura pública de logos) — baixa sensibilidade; decisão de produto.
