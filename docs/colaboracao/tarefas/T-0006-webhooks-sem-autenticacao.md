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
