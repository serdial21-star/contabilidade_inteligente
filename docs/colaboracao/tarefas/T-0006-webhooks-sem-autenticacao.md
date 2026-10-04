# T-0006 — Webhooks ativos sem autenticação e sessão revogada aceita (inventário do n8n)

| Campo | Valor |
|---|---|
| Estado | CI VERDE — aguardando publicação guiada |
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

### [2026-10-03] Codex — Revisão da proposta (transcrita pelo Claude a partir da mensagem repassada pelo usuário)

Aprova a direção, inclusive desativar `admin/tasks` e remover só o webhook do motor. Exige no briefing: (1) `upload-xml`/`apuracao-icms` com sessão viva e não revogada **e** permissão do funcionário **e** acesso ao cliente indicado, sem que `cliente_id` autorize a si mesmo; (2) `honorarios-v2` com `revogado_em IS NULL`, mantendo o cliente vindo da sessão; (3) segredo do Colab aleatório, rotacionável, só em credencial do n8n e Secrets do Colab, rejeição antes de qualquer gravação; (4) `ai-analyst` prioritário, validando sessão e autorização da ferramenta, alterando também o chamador; (5) chamado sem usuário autenticado deve ser bloqueado com mensagem, não enviado com outra identidade; (6) item 20 fora da T-0006; (7) restringir também `proxy-file-upload`, com lista exata path + método e destino montado no servidor (OWASP SSRF); (8) seguir o protocolo normal (Codex implementa, Claude revisa) ou registrar exceção com revisão independente; (9) registrar expressamente a aprovação que muda a decisão "os cinco serão usados".

### [2026-10-03] Claude — Análise da revisão do Codex

- **Concordo** com 2, 3, 4, 5, 6, 8 e 9, e com 1 quanto a sessão viva, não revogada e permissão do módulo.
- **Motor (verificado na exportação):** o cron (`5 6 * * *`) e o webhook ligam ambos direto ao primeiro nó SQL, e nenhum nó referencia dados do webhook — remover o webhook não afeta o cron. O workflow não define timezone próprio; vale o `GENERIC_TIMEZONE` do container, ainda não conferido.
- **`honorarios-v2` (verificado):** o cliente já vem da sessão (`SQL validar token` → `cliente_id`); falta só `revogado_em IS NULL`. O SQL é por interpolação; o token é saneado para alfanumérico antes.
- **Item 7 — parcialmente divergente:** o inventário do Lovable registra que `proxy-file-upload` **já tem** lista de paths (`["/ferramentas-ia/apuracao-icms"]`) e `verify_jwt = true`; quem não tem lista é o `proxy-webhook`. Não há evidência de destino arbitrário no `proxy-file-upload`. Ainda assim, cabe como critério de aceite **verificar** que o destino é montado a partir de base constante + path exato + método, sem aceitar URL do cliente — ajustando só se não for.
- **Item 1 — acesso ao cliente é lacuna de política, não regra existente:** a autorização vigente (ADR 0018, T-0003) é por módulo/ação; nenhuma operação administrativa hoje restringe funcionário por cliente via `permissoes_funcionario_clientes`, e o significado de "nenhuma linha" nessa tabela não está definido. Impor isso só no `upload-xml` seria inventar regra e criaria comportamento inconsistente entre telas. Proposta: nesta tarefa, sessão + permissão do módulo + cliente existente; acesso por cliente vira decisão do usuário (e, se aprovado, ADR própria para todo o painel).
- **Acréscimo:** os workflows tocados devem passar a usar consultas parametrizadas (o `integracao-cnd` interpola `cnpj` no SQL).
- **Contenção imediata possível sem implementação:** desativar `admin/tasks` (aprovado, reversível).

### [2026-10-03] Usuário
- "aprovo formalmente desativar" — aprova desativar `admin/tasks` e remover somente o webhook do motor de obrigações (o cron diário permanece). Substitui, para esses dois, a decisão anterior "todos serão utilizados".
- Concorda com as demais orientações: fluxo normal do protocolo (Codex implementa, Claude revisa); acesso por cliente fora desta tarefa, como decisão futura para todo o painel; demais pontos da análise do Claude.
- Matriz de permissões (consulta agregada, primeiras 25 de 40 linhas): o módulo `ferramentas_ia` existe; `ferramentas_ia/criar` liberado para os 7 funcionários.

---

## 1. Briefing (Claude)

### [2026-10-03] Claude — Briefing para o Codex

**Problema.** Ver Diagnóstico e Cruzamento acima. Endpoints do Sistema A que produzem efeito ou expõem dados sem autenticação/autorização no servidor, sessão revogada aceita em `portal/honorarios-v2`, função de IA consumível com a chave pública e proxy sem lista de destinos.

**Objetivo.** Toda chamada a esses endpoints passa a exigir, no servidor e antes de qualquer efeito, a credencial adequada (sessão de funcionário viva e não revogada com permissão de módulo; sessão de cliente viva e não revogada; ou segredo de integração), e os proxies só encaminham destinos previamente listados.

**Base versionada.**
- Workflows como estão hoje em produção (exportação de 03/10/2026, sem o campo `shared` com dados do dono da conta): `docs/integration/system_a_webhook_hardening/baseline/`.
- Inventário do site: `docs/integration-input/INVENTARIO_LOVABLE_2026-10-03.md`.
- Padrões a seguir: T-0003 (`docs/integration/system_a_client_management/`, ADR 0018) e T-0005 (`docs/integration/system_a_session_logout/`).

**Escopo — dentro.** Artefatos novos em `docs/integration/system_a_webhook_hardening/`:
1. **Migration `005_up.sql`/`005_down.sql`** com uma autorização genérica de funcionário por módulo/ação para uso fora de clientes (não alterar as procedures da T-0003 já publicadas). Mesmas regras da D1 da T-0003: sessão com `revogado_em IS NULL` e `expira_em > UTC_TIMESTAMP()`, funcionário `Ativo`, cargo `Administrador`/`Admin` (sem diferenciar maiúsculas, sem espaços nas pontas) sempre autorizado, demais só com `permitido = 1` para `(modulo, acao)`; sem linha, `permitido = 0`, cargo vazio ou desconhecido → negado. `SQL SECURITY INVOKER`, token validado por formato (`^[0-9A-Za-z]{20,128}$`), hash comparado com a colação da coluna (lição da T-0005), resultado em uma linha (`success`, `result` ∈ `authorized`/`unauthorized`/`forbidden`, `funcionario_id`), auditoria mínima da negação `forbidden` sem token nem hash, com nome de ação próprio (não reutilizar `client_action_forbidden`). Rollback remove só os objetos da 005. `verify_005.sql` somente leitura.
2. **`admin/upload-xml`** (a partir de `baseline/n8n_admin_upload_xml_v7.json`): primeiro passo chama a autorização com módulo `ferramentas_ia` e ação `criar`; `unauthorized` → 401, `forbidden` → 403, sem tocar Drive nem banco. `cliente_id` precisa ser inteiro positivo de cliente existente (senão 400/404 sem efeito); ele não autoriza a operação. Todas as consultas parametrizadas (`queryReplacement`), inclusive a gravação em `processamento_xml_nfe`. CORS restrito a `https://serdial21.com`.
3. **`ferramentas-ia/apuracao-icms`** (a partir de `baseline/n8n_ferramentas_ia_apuracao_icms_v9.json`): mesma autorização (`ferramentas_ia`, `criar`) antes de qualquer operação no Drive/Sheets; o token chega como `Authorization: Bearer` (a função `proxy-file-upload` converte o `x-app-token`).
4. **`portal/honorarios-v2`** (a partir de `baseline/n8n_portal_honorarios_v2.json`): a validação da sessão de cliente passa a exigir `revogado_em IS NULL`; o `cliente_id` continua vindo só da sessão; consultas parametrizadas; CORS restrito.
5. **`admin/integracao-cnd-v1`** (a partir de `baseline/n8n_admin_integracao_cnd_v1.json`): autenticação do próprio nó Webhook por **Header Auth** com credencial do n8n (cabeçalho com nome definido no artefato; valor nunca versionado), de modo que a rejeição ocorra antes de qualquer nó; consultas parametrizadas (hoje `cnpj` é interpolado); CNPJ tratado como string, preservando zeros à esquerda.
6. **Motor de obrigações** (a partir de `baseline/n8n_gerador_obrigacoes_auto_v1.json`): remover o nó "Webhook - Executar Manual" e sua conexão; nada mais muda. Não alterar fuso: o valor de `GENERIC_TIMEZONE` do container será informado pelo usuário e registrado; se divergir do esperado, é decisão do usuário.
7. **Prompt para o Lovable** (`LOVABLE_PROMPT.md`):
   - `ai-analyst`: o chamador passa a enviar `x-app-token` com `admin_auth_token` (como `sistema-b-bridge-token`); a função valida a sessão e a permissão `ferramentas_ia`/`criar` no servidor antes de chamar o gateway de IA (modelo: `client-logo`, que consulta `admin/permissoes/funcionario`; cargo Administrador/Admin autorizado), e responde 401/403 sem chamar a IA;
   - `proxy-webhook`: lista exata de **path + método** permitidos, igual ao conjunto de chamadas via proxy do inventário; destino montado no servidor a partir de base constante; qualquer outro → 404 sem encaminhar; manter `verify_jwt = false` (o `Authorization` leva o token do Serdial21, não um JWT do Supabase) — registrar a justificativa;
   - `proxy-file-upload` e `proxy-document-download`: **verificar** e, só se necessário, ajustar para que o destino seja base constante + path exato + método, sem aceitar URL do cliente;
   - remover a busca "legado" da Biblioteca (`listar-arquivos`);
   - `HelpdeskTicketForm`: sem usuário autenticado, bloquear o envio com mensagem para entrar no sistema; nunca usar e-mail fixo ou outra identidade.
8. **Trecho para o Google Colab** (`COLAB_SNIPPET.md`): enviar o cabeçalho de integração lendo o valor dos Secrets do Colab (`google.colab.userdata`), sem valor no notebook.
9. **Runbook** `docs/integration/SYSTEM_A_WEBHOOK_HARDENING_RUNBOOK.md` com publicação e rollback (abaixo).

**Escopo — fora.** Item 20 (endpoints inexistentes); acesso por cliente (`permissoes_funcionario_clientes`); demais workflows já autenticados; troca de `NOW()` nos workflows não tocados; logins (item 7); `admin/tasks` (só desativação, ação do usuário); bucket `client-logos`.

**Restrições.** `AGENTS.md` 6.4 (autorização no servidor; ID não autoriza), 6.7 (efeito e auditoria na mesma transação; nada de efeito antes da autorização), 6.9 (nenhum segredo versionado), 6.10; ADR 0018 (D1 e fail-closed); OWASP Authorization Cheat Sheet (verificação no servidor a cada requisição) e OWASP SSRF Prevention Cheat Sheet (lista de destinos e URL montada no servidor) — citar data de acesso nos artefatos.

**Critérios de aceite.**
1. Sem token, token malformado, sessão inexistente, expirada ou revogada → 401 em `upload-xml` e `apuracao-icms`, sem nenhum nó de Drive, Sheets ou banco executado depois da autorização.
2. Funcionário ativo sem `ferramentas_ia`/`criar` → 403 sem efeito, com auditoria da negação; Administrador/Admin → autorizado.
3. `upload-xml` com `cliente_id` inválido ou inexistente → erro sem efeito.
4. `honorarios-v2` recusa sessão de cliente revogada; o cliente consultado é sempre o da sessão.
5. `integracao-cnd-v1` sem o cabeçalho ou com valor errado → rejeitado pelo n8n antes de qualquer nó.
6. Motor: só o webhook foi removido; o cron e os nós SQL estão idênticos ao baseline.
7. Nenhuma consulta dos workflows alterados interpola valor vindo da requisição.
8. Nenhum segredo, token, e-mail real ou dado de cliente nos artefatos; `saveDataSuccessExecution`/`saveDataErrorExecution = none`; workflows exportados inativos e sem credenciais.
9. Rollback da 005 remove só seus objetos.

**Testes exigidos.**
- Validador MariaDB do CI (estender o existente): autorização genérica com Administrador, Admin com espaços, Operador com e sem permissão, `permitido = 0`, sem linha, cargo vazio/desconhecido, funcionário inativo, sessão expirada, revogada, inexistente e token malformado; auditoria só na negação `forbidden`, sem token/hash; rollback.
- Testes estáticos dos JSONs (como `tests/unit/test_system_a_*`): ordem dos nós (autorização antes de qualquer efeito), mapeamento 401/403, parâmetros sem interpolação, Header Auth no CND, ausência do webhook no motor com o resto idêntico ao baseline, CORS sem `*`, sem retenção, sem credenciais.
- Testes do prompt/snippet: presença das regras obrigatórias (lista path+método, 401/403 antes da IA, bloqueio sem usuário, segredo lido de Secrets).

**Riscos.**
- Funcionário que usa as ferramentas sem `ferramentas_ia`/`criar` perde acesso — hoje os 7 têm.
- A troca do CND exige publicar o workflow e atualizar o Colab juntos; entre um e outro as gravações do Colab falham (sem perda: o Colab pode reenviar).
- A lista do `proxy-webhook` pode bloquear uma chamada que o inventário não captou: testar todas as telas depois.
- Os endpoints do item 20 continuam inexistentes; não incluí-los na lista não muda o comportamento atual (já falham).

**Ações do usuário.**
- Já: desativar "Serdial21 - Admin Tasks Kanban v1.0" (renomear com "(DESATIVADO 2026-10-03)"); informar `docker exec n8n-n8n-1 printenv GENERIC_TIMEZONE TZ`.
- Depois do CI verde e do aceite: publicação conforme o runbook — `verify_005` → backup → `005_up` → workflows (honorários, upload-xml, apuração, motor) → credencial Header Auth + workflow CND + Secret do Colab, juntos → Lovable (revisar o diff) → teste de todas as telas do painel e do portal.
- Rollback por peça: reativar o workflow anterior (renomeado, não apagado); `005_down.sql`; reverter publicação no Lovable.

---

## 2. Decisões do usuário (continuação)

### [2026-10-03] Usuário
- "aprovo o briefing da T-0006" — inclui a exigência de `ferramentas_ia`/`criar` para executar as três ferramentas de IA.

---

## 3. Implementação (Codex)

(aguardando "execute a tarefa T-0006")

### [2026-10-03] Usuário (registrado pelo Claude)
- Workflow "Serdial21 - Admin Tasks Kanban v1.0" (`admin/tasks`) desativado.
- Fuso do n8n: `GENERIC_TIMEZONE`/`TZ` informado como America/Sao_Paulo. O cron do motor de obrigações (`5 6 * * *`) roda às 06:05 no horário de Brasília; nenhuma mudança de fuso é necessária no item 6 do briefing.

### [2026-10-03] Codex — Implementação

**Resultado.** Implementei os artefatos aprovados sem executar contra serviços reais. A migration 005 centraliza a autorização genérica de funcionário por módulo/ação, com sessão viva e não revogada, funcionário ativo, bypass restrito a `Administrador`/`Admin`, matriz fail-closed e auditoria mínima de `forbidden`. `upload-xml` e `apuracao-icms` chamam essa fronteira antes de qualquer efeito e mapeiam `unauthorized`/`forbidden` para 401/403. Honorários recusa sessão revogada. CND usa Header Auth e consultas parametrizadas. O motor preserva o cron e remove somente o webhook.

**Arquivos criados.**

- `docs/integration/system_a_webhook_hardening/005_up.sql`;
- `docs/integration/system_a_webhook_hardening/005_down.sql`;
- `docs/integration/system_a_webhook_hardening/verify_005.sql`;
- `docs/integration/system_a_webhook_hardening/n8n_admin_upload_xml_v7_hardened.json`;
- `docs/integration/system_a_webhook_hardening/n8n_ferramentas_ia_apuracao_icms_v9_hardened.json`;
- `docs/integration/system_a_webhook_hardening/n8n_portal_honorarios_v2_hardened.json`;
- `docs/integration/system_a_webhook_hardening/n8n_admin_integracao_cnd_v1_hardened.json`;
- `docs/integration/system_a_webhook_hardening/n8n_gerador_obrigacoes_auto_v1_cron_only.json`;
- `docs/integration/system_a_webhook_hardening/LOVABLE_PROMPT.md`;
- `docs/integration/system_a_webhook_hardening/COLAB_SNIPPET.md`;
- `docs/integration/SYSTEM_A_WEBHOOK_HARDENING_RUNBOOK.md`;
- `tests/unit/test_system_a_webhook_hardening_assets.py`.

**Arquivos alterados.**

- `scripts/validate_system_a_client_management.sh`: aplica/testa/reverte a 005 no MariaDB descartável do CI;
- `docs/colaboracao/QUADRO.md`: tarefa encaminhada para revisão;
- este arquivo, somente por acréscimo deste relatório.

**Detalhes técnicos.**

- Os cinco JSONs são importáveis, inativos, sem credenciais e com retenção de execução desabilitada. O runbook exige reassociar credenciais antes da ativação.
- `upload-xml`: token Bearer estrito; `CALL sp_admin_module_authorize` com `ferramentas_ia/criar`; validação de `cliente_id` inteiro positivo e cliente existente; binário restaurado somente no ramo autorizado; consultas MySQL com `queryReplacement`; CORS restrito.
- `apuracao-icms`: mesma autorização e restauração do binário antes do extrator; 401/403 encerram o fluxo antes de Drive/Sheets.
- `honorarios-v2`: token estrito, `revogado_em IS NULL`, `UTC_TIMESTAMP()`, cliente somente da sessão e três consultas parametrizadas.
- CND: Webhook em `headerAuth`, com nota que fixa `X-Serdial21-Integration-Secret`; valor ausente do artefato; CNPJ permanece string; busca e upsert parametrizados.
- Motor: teste compara estruturalmente com o baseline e permite apenas a remoção do nó `Webhook - Executar Manual`, da conexão correspondente, das credenciais/metadados de exportação e os ajustes obrigatórios de retenção/inatividade.
- Prompt Lovable exige autenticação/autorização antes da IA, allowlist exata `path + método`, destino montado no servidor, verificação dos proxies especializados, remoção de `listar-arquivos` e bloqueio do chamado sem sessão.
- `GENERIC_TIMEZONE`/`TZ` foi confirmado como `America/Sao_Paulo`; o cron `5 6 * * *` foi preservado sem alteração.
- Nenhuma migration Alembic foi criada. A única migration é a `005` externa do Sistema A.

**Testes executados.**

- `tests/unit/test_system_a_webhook_hardening_assets.py`: **12 passed**.
- T-0003 + T-0005 + T-0006: **46 passed**.
- suíte local sem os seis módulos API que não coletam por falta do pacote `redis`: **536 passed, 20 skipped**.
- suíte completa sem exclusões: interrompida na coleta dos mesmos seis módulos por `ModuleNotFoundError: redis`; limitação local preexistente, sem relação com o diff.
- `scripts/verify_release_secrets.py`: `RELEASE_SECRET_SCAN: PASS` e canário detectado.
- `bash -n scripts/validate_system_a_client_management.sh`: aprovado com Git Bash.
- `git diff --check`: aprovado; somente aviso de futura conversão LF/CRLF no script.

**Não executado.** O validador MariaDB descartável não rodou porque o Docker Desktop local não está iniciado. A execução real de `005_up.sql`, cenários de autorização e `005_down.sql` fica pendente no CI. Nenhum banco, API, n8n, Supabase, Lovable, Colab ou VPS real foi acessado.

**Pendências para revisão/publicação.**

1. Claude revisar o diff real e os artefatos; CI deve emitir `WEBHOOK_HARDENING_AUTHORIZATION_TESTS=PASS` e `WEBHOOK_HARDENING_ROLLBACK=PASS`.
2. Após aceite, seguir `SYSTEM_A_WEBHOOK_HARDENING_RUNBOOK.md`, reassociar credenciais, aplicar o prompt no Lovable e revisar o diff produzido pelo Lovable antes de publicar.

---

## 4. Revisão (Claude)

### [2026-10-03] Claude — Revisão da implementação

Diff lido por inteiro (artefatos novos, `scripts/validate_system_a_client_management.sh`, testes). Testes relacionados rodados pelo Claude: `49 passed` (T-0003, T-0004, T-0005, T-0006); varredura de segredos `PASS`. Validador MariaDB não executado localmente (sem Docker), pendente no CI.

**Verificado e correto.**
- `005_up.sql`: sessão viva, não revogada, em UTC; funcionário `Ativo`; bypass só para `administrador`/`admin` com `BINARY` após `LOWER(TRIM(...))` (não aceita variações acentuadas pela colação `_ci`); sem linha ou `permitido <> 1` → `forbidden`; auditoria só em `forbidden`, com `request_id`, módulo e ação, sem token nem hash; hash em variável com a colação da coluna; `005_down.sql` remove só a procedure.
- `upload-xml`: autorização é o primeiro passo depois do webhook; 401/403/400/404 encerram antes de Drive e banco; o `cliente_id` usado adiante é o validado (sobrescrito em "Restaurar Upload Autorizado"; "Separar XMLs" idêntico ao baseline); consultas com `queryReplacement`; leitura da autorização ignora o pacote de status do `CALL` (lição da T-0003).
- `apuracao-icms`: autorização antes do extrator, Drive e Sheets.
- `honorarios-v2`: `revogado_em IS NULL`, `UTC_TIMESTAMP()`, cliente só da sessão, consultas parametrizadas; com `alwaysOutputData` a sessão inexistente agora responde 401 (antes o fluxo parava sem resposta).
- CND: `headerAuth` no próprio Webhook (rejeição antes de qualquer nó); busca e upsert parametrizados, CNPJ como string. Mudanças de comportamento aceitas: CNPJ com `trim`/maiúsculas antes da busca; `updated_at` com `UTC_TIMESTAMP()` em vez de `NOW()` (equivalente em produção, que roda em UTC — T-0005).
- Motor: diferença estrutural com o baseline = só o nó "Webhook - Executar Manual" e sua conexão.
- Todos os JSONs inativos, sem credenciais, sem retenção, CORS restrito.
- Validador: bloco da 005 roda antes dos testes da 003 e da 004 e restaura o estado das sessões que altera; não interfere nas contagens de auditoria existentes (`client_action_forbidden`).

**Ajustes exigidos antes do aceite.**

1. **(ALTA) `LOVABLE_PROMPT.md`, seção 1, item 5 — autorização do `ai-analyst` com dado que o servidor não devolve.** O prompt manda autorizar "cargo `Administrador`/`Admin` ... ou `permitido = 1` para `ferramentas_ia`/`criar`" a partir da resposta de `admin/permissoes/funcionario`. Essa resposta (nó "Montar Permissões", `docs/integration/system_a_permissions/n8n_admin_permissoes_funcionario_v2_2.json`) devolve só `success`, `modulos` (booleanos) e `clientesAcesso` — **não devolve cargo**. Para cumprir a instrução, o Lovable tende a ler o cargo de `admin_user` no `localStorage`, que o próprio usuário controla: qualquer funcionário poderia se declarar Administrador e usar a IA. Corrigir para: autorizar **somente** se a resposta do servidor tiver `success === true` e `modulos.ferramentas_ia.criar === true`; proibir explicitamente usar `admin_user`, cargo ou qualquer dado do navegador na decisão. Registrar no prompt que os Administradores atuais passam por terem a linha `ferramentas_ia/criar` (o fallback por cargo daquele workflow não inclui `ferramentas_ia`; um Administrador sem linhas receberia 403 — comportamento fail-closed aceitável, a registrar no runbook).
2. **(MÉDIA) `LOVABLE_PROMPT.md`, seção 2 — método efetivo.** O `proxy-webhook` escolhe o método encaminhado pelo campo `_method` (inventário, seções 2 e 4; `useListas`). A allowlist precisa comparar o **método efetivamente encaminhado** (depois de aplicar `_method`), e só aceitar `_method` com valores da própria lista para aquele path; caso contrário um `POST` permitido poderia sair como `DELETE`. Explicitar.
3. **(BAIXA) Validador:** incluir `SyntheticAccentedRoleToken11` no laço de `forbidden` da 005, cobrindo o `BINARY` (o caso existe para a 003 e não para a 005).
4. **(BAIXA) Runbook, pré-publicação item 5:** dizer como gerar o segredo fora do repositório (por exemplo, `python -c "import secrets; print(secrets.token_urlsafe(32))"` na máquina do usuário, sem colar em chat ou arquivo) e acrescentar ao teste do Lovable a verificação de que um Administrador sem a linha `ferramentas_ia/criar` recebe 403 (efeito do item 1).

**Veredito: AJUSTES PEDIDOS.** Itens 1 e 2 bloqueiam o aceite; 3 e 4 entram no mesmo ciclo. Nenhuma mudança nos workflows nem na 005. Depois do ajuste: nova revisão, commit pelo Claude, push pelo usuário e CI com `WEBHOOK_HARDENING_AUTHORIZATION_TESTS=PASS` e `WEBHOOK_HARDENING_ROLLBACK=PASS`.

### [2026-10-03] Codex — Resposta à revisão

Os quatro ajustes foram atendidos sem alterar os workflows nem a migration 005.

1. **Autorização do `ai-analyst`:** o prompt agora autoriza somente quando a resposta do servidor contém `success === true` e `modulos.ferramentas_ia.criar === true`. Proíbe expressamente usar `admin_user`, `localStorage`, cargo ou qualquer dado do navegador. Registra o comportamento fail-closed: Administrador sem linha explícita recebe 403 sem chamar o gateway.
2. **Método efetivo do `proxy-webhook`:** o prompt agora exige resolver `_method` antes da allowlist, normalizar o método efetivamente encaminhado e validar a combinação exata com o path. `_method` inválido ou não permitido retorna 404 sem `fetch`; o método validado é o mesmo usado na chamada ao n8n.
3. **Cargo acentuado:** `SyntheticAccentedRoleToken11` entrou no laço `forbidden` da 005. As três contagens de `employee_module_action_forbidden` foram atualizadas de 6 para 7.
4. **Runbook:** inclui comando local para gerar segredo com `secrets.token_urlsafe(32)`, instrução para não copiar o valor em chat/arquivo/tarefa/log e teste explícito de 403 para Administrador sem `ferramentas_ia/criar` no `ai-analyst`.

**Testes atualizados.** Os testes estáticos agora exigem a autorização exclusivamente server-side, a validação do método efetivo, o caso do cargo acentuado, a geração segura do segredo e o teste fail-closed do Administrador.

**Validação.** T-0006: `12 passed`; conjunto T-0003–T-0006: `49 passed`; suíte local disponível: `536 passed, 20 skipped`; sintaxe do shell e `git diff --check`: aprovados; varredura de segredos: `PASS`. O validador MariaDB continua pendente no CI porque o Docker Desktop local não está iniciado.

### [2026-10-03] Claude — Nova revisão e aceite

- Ajuste 1: seção 1, item 5 do `LOVABLE_PROMPT.md` autoriza só por `success === true` e `modulos.ferramentas_ia.criar === true` vindos do servidor; proíbe `admin_user`, `localStorage` e cargo; registra o 403 para Administrador sem a linha. Atendido.
- Ajuste 2: seção 2 exige resolver `_method`, normalizar e validar o método efetivamente encaminhado contra a combinação exata; o `fetch` usa o método validado. Atendido.
- Ajuste 3: `SyntheticAccentedRoleToken11` no laço `forbidden` da 005; contagens 6 → 7 nos três pontos. Atendido.
- Ajuste 4: runbook com geração local do segredo (`secrets.token_urlsafe(32)`), proibição de copiar o valor e teste de 403 do Administrador no `ai-analyst`. Atendido.
- Testes relacionados rodados pelo Claude: `49 passed`; sintaxe do validador aprovada. Workflows e 005 sem alteração desde a primeira revisão (o Codex declarou; os testes estáticos que os cobrem continuam passando).

**Veredito: ACEITA.** Condição para publicar: CI verde com `WEBHOOK_HARDENING_AUTHORIZATION_TESTS=PASS` e `WEBHOOK_HARDENING_ROLLBACK=PASS` (primeira execução real da 005).

### [2026-10-03] Claude — Credencial da Meta (item D do diagnóstico)

Conferida pelo usuário no depurador oficial da Meta (valor não transcrito): token do tipo User, app "Automação Serdial21", escopos de WhatsApp Business, **Válido: Falso**, expirado em 03/03/2026. Não há o que revogar; resta apagar o valor dos três nós do workflow inativo "Automação - Finalizar Ticket" (ou excluí-lo). Nenhum workflow ativo usa a API do WhatsApp. Chave do Google (Cloud Vision): pendente.

### [2026-10-03] Claude — Credenciais, limpeza e CI verde

- Usuário: chave do Google excluída e valores removidos dos nós dos dois workflows inativos ("apagado, tudo feito"). Item D do diagnóstico encerrado.
- A cópia da exportação dos 149 workflows foi apagada da pasta temporária do Claude, com autorização do usuário. No repositório ficam só os cinco baselines, sem segredos e sem o campo `shared`.
- CI verde no commit `db66ac4` (run 37164674045), conferido no log: `538 passed`; `CLIENT_MANAGEMENT_ROLLBACK=PASS`; `SESSION_LOGOUT_TESTS=PASS`; `SESSION_LOGOUT_ROLLBACK=PASS`; `WEBHOOK_HARDENING_AUTHORIZATION_TESTS=PASS` e `WEBHOOK_HARDENING_ROLLBACK=PASS` (primeira execução real da 005 no MariaDB 11.8.9); `pip-audit` sem vulnerabilidades; varredura de segredos `PASS`.

**Próximo passo:** publicação guiada pelo `docs/integration/SYSTEM_A_WEBHOOK_HARDENING_RUNBOOK.md`.
