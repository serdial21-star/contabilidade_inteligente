# T-0008 — Portal do cliente: detalhe e complemento de chamados e documentos

| Campo | Valor |
|---|---|
| Estado | APROVADA — aguardando implementação pelo Codex |
| Origem | QUADRO, fila item 20 (primeira parte); escolhida pelo usuário em 04/10/2026 para destravar os testes práticos com clientes |
| Sistema | Sistema A (n8n, MySQL, frontend Lovable) |
| Exige ADR | não — decisões D1–D5 registradas aqui; migration 006 não destrutiva |
| Exige ação do usuário | sim — prompt somente leitura no Lovable, consultas somente leitura no banco, exportação de workflows |

---

## 1. Diagnóstico (Claude)

### [2026-10-04] Claude — Ponto de partida

**Problema.** Segundo o inventário do Lovable (`docs/integration-input/INVENTARIO_LOVABLE_2026-10-03.md`, seção 2) e o cruzamento com a exportação do n8n (T-0006), o portal chama pelo `proxy-webhook` quatro endpoints que **não existem** no n8n: `POST /portal/detalhe-chamado`, `POST /portal/complementar-chamado`, `POST /portal/detalhe-documento`, `POST /portal/complementar-documento` (TicketDetailDrawer e DocumentDetailDrawer). A lista de chamados e de documentos funciona (`/portal/meus-chamados-v2`, `/portal/meus-documentos-v2`), mas abrir o detalhe ou complementar falha. As quatro combinações já estão na allowlist do proxy (T-0006).

**Fora desta tarefa** (continuam no item 20): abas Certidões, Livros e Obrigações da Biblioteca; Inteligência Fiscal (`admin/fiscal/*`).

**Informações necessárias antes do briefing.**
1. **Contrato esperado pela tela** — prompt somente leitura: `docs/integration-input/PROMPT_LOVABLE_DETALHE_CHAMADOS_DOCUMENTOS_2026-10-04.md`.
2. **Estrutura do banco** — consultas somente leitura (colunas, sem dados) das tabelas de chamados, documentos e possíveis tabelas de mensagens, anexos e histórico.
3. **Workflows existentes que já leem/gravam esses dados**, para reaproveitar regras e manter um único modelo: "API - Portal - Consultas V2 (Robusto)" (`portal/meus-chamados-v2`, `portal/meus-documentos-v2`), "[CRUD] Receber Ticket do Portal V2 (Completo) (Corrigido)" (`portal/abrir-ticket-v2`), "[CRUD] Receber Arquivo do Portal V2 (Seguro) (Token Seguro)" (`portal/receber-arquivo-v2`), "API - Admin - Responder Ticket (Com Sessão, com mensagens)" (`admin/responder-ticket-v2`) e "API - Admin - Listagens Gerais V2 (Corrigido)" (`admin/tickets-v2`, `admin/documentos-v2`).

**Requisitos já conhecidos (de `AGENTS.md` e das tarefas anteriores)**, que o briefing vai exigir: sessão de cliente viva e não revogada; o cliente consultado é **sempre** o da sessão — `id` de chamado/documento vindo da tela não autoriza nada e outro cliente recebe a mesma resposta de "não encontrado"; SQL parametrizado; CORS restrito; sem retenção de execuções; complemento com arquivo grava no Drive do próprio cliente; trilha de auditoria do complemento.

### [2026-10-04] Claude — Leitura dos cinco workflows existentes (enviados pelo usuário; não versionados)

Sem segredos (apenas nomes/ids de credenciais). Achados:

- **Modelo de dados de chamados já existe e o painel já o usa:**
  - `tickets_master` (id, cliente_id, numero_ticket, assunto, descricao, status, area, prioridade, criado_em, atualizado_em);
  - `tickets_mensagens` (ticket_id, remetente_tipo `'Equipe'`/cliente, remetente_id, mensagem, anexo_url, criado_em) — "API - Admin - Listagens Gerais V2" devolve cada ticket com `historico: [{data, autor, mensagem, tipo}]`; "API - Admin - Responder Ticket" grava em `tickets_mensagens` com `remetente_tipo = 'Equipe'` e atualiza `tickets_master.status`/`atualizado_em`, com auditoria `EDITAR`;
  - anexos de chamado: "[CRUD] Receber Ticket do Portal V2" envia ao Drive na subpasta da área (roteador `01_FISCAL`/`02_PESSOAL`/`03_CONTABIL`/`04_SOCIETARIO`/`99_DIVERSOS`) e registra em `evidencias_protocolos` (cliente_id, nome_evidencia, tipo, link_arquivo, ticket_id).
  - Consequência: detalhe e complemento de chamado no portal podem reaproveitar `tickets_mensagens` (lado cliente) — conferir o valor de `remetente_tipo` usado para o cliente e se `remetente_id` guarda `cliente_id`.
- **Documentos:** `inbox_documentos` (id, cliente_id, titulo, area_responsavel, competencia, status, nome_arquivo, tipo_documento, link_externo_url, criado_em). Nenhum workflow lido grava conversa/complemento de documento; aguardando a consulta ao banco para saber se existe tabela própria.
- **Observações de segurança nos workflows existentes (fora do escopo; registrar na fila):** CORS `*` e SQL por interpolação nos cinco; `NOW()` na validação de sessão; "Listagens Gerais V2" e "Responder Ticket" validam só a sessão de funcionário, sem permissão de módulo (`tickets`/`documentos`); "Listagens Gerais V2" devolve todos os chamados e documentos de todos os clientes sem filtro; número de ticket gerado com `Math.random`.
- Pendentes para o briefing: relatório do Lovable (contrato das quatro chamadas) e estrutura das tabelas (consulta ao `information_schema`).

### [2026-10-04] Claude — Estrutura do banco e contrato da tela (recebidos do usuário)

- `information_schema` (colunas, sem dados): `tickets_mensagens` (id, ticket_id, `remetente_tipo enum('Cliente','Equipe')`, `remetente_id int NOT NULL`, mensagem text NOT NULL, `anexo_url varchar(255)`, criado_em) — **sem coluna de nome do anexo**; `inbox_documentos` (id, titulo, area_responsavel, competencia, tipo_documento, link_externo_url, status, `observacao_escritorio`, `observacao_cliente`, ticket_id, entrega_id, cliente_id, criado_em, atualizado_em, origem_documento, nome_arquivo) — **sem tabela de complementos de documento**; `tickets_master` (inclui competencia, data_limite, pessoa_responsavel, data_entrega, responsavel_interno).
- Relatório do Lovable (somente leitura): as quatro chamadas saem pelo `portalFetch` → `proxy-webhook` (`POST`, JSON, `Authorization: Bearer auth_token`); tipos `Chamado`, `Documento`, `Complemento {id, mensagem, arquivo_url?, arquivo_nome?, criado_em, autor?, tipo?: 'cliente'|'equipe'}`; respostas `{success, data}` e `{success, message?}`; complemento envia `{ticket_id|documento_id, mensagem, arquivo_base64?: 'data:<tipo>;base64,...', arquivo_nome?}`, um arquivo por envio, a tela não valida tipo nem tamanho; chamado fechado quando `status` = `concluído`/`concluido`; documento fechado quando `processado`/`concluído`/`rejeitado`; painel usa `historico` (sem anexo) em `/admin/tickets-v2` e não tem tela de complementos de documento.

---

## 1. Briefing (Claude)

### [2026-10-04] Claude — Briefing para aprovação

**Objetivo.** No portal, o cliente vê o detalhe e o histórico de chamados e documentos e consegue complementá-los (mensagem e/ou um anexo); a equipe vê esses complementos no painel; tudo isolado por cliente, auditado e sem retenção.

**Decisões propostas (precisam do usuário).**
- **D1 — Complementos de documento em tabela própria** (`inbox_documentos_complementos`: id, documento_id, cliente_id, remetente_tipo `Cliente`/`Equipe`, remetente_id, mensagem, anexo_url, anexo_nome, criado_em), append-only, criada por migration `006`. Alternativa rejeitada: gravar em `inbox_documentos.observacao_cliente` (sobrescreve, perde histórico — contraria `AGENTS.md` 6.7).
- **D2 — Nome do anexo em `tickets_mensagens`**: nova coluna anulável `anexo_nome varchar(255)` na mesma migration `006` (não destrutiva; linhas antigas ficam nulas).
- **D3 — Arquivos aceitos**: PDF, JPG/JPEG e PNG (e XML nos documentos), conferidos pelo conteúdo (assinatura do arquivo), não só pela extensão; **tamanho máximo a definir** — proposta 10 MB, limitada ao menor limite técnico do caminho (Edge Function e n8n), que o Codex deve verificar e registrar.
- **D4 — Complemento do cliente não muda o status** do chamado/documento; só atualiza `atualizado_em` e aparece no histórico. Mudança automática de status seria regra nova sem fonte.
- **D5 — A equipe passa a ver os complementos de documento no painel**: `admin/documentos-v2` devolve o histórico de cada documento e um prompt do Lovable mostra esse histórico no painel de documentos. Sem isso, complementos de documento ficariam invisíveis para a equipe.

**Escopo — dentro** (artefatos em `docs/integration/system_a_portal_detalhes/`):
1. Migration `006_up.sql`/`006_down.sql`/`verify_006.sql` (D1, D2), com procedures `SQL SECURITY INVOKER` para as quatro operações do portal, no padrão das 003–005: sessão de cliente viva e não revogada (UTC); cliente **sempre** o da sessão; `ticket_id`/`documento_id` inteiro positivo; recurso de outro cliente ou inexistente → mesmo resultado `not_found`; complemento recusado se o item estiver fechado (`closed`); mensagem até 5000 caracteres; complemento exige mensagem ou anexo; inserção, `atualizado_em` e auditoria (`client_ticket_complement`/`client_document_complement`, sem conteúdo da mensagem) na mesma transação.
2. Quatro workflows n8n (`portal/detalhe-chamado`, `portal/complementar-chamado`, `portal/detalhe-documento`, `portal/complementar-documento`): token só do `Authorization`; consultas parametrizadas; anexo decodificado do base64, tipo verificado pelo conteúdo e tamanho conferido **antes** de qualquer gravação; upload ao Drive do próprio cliente na subpasta da área (mesmo roteador dos workflows atuais); a procedure grava o registro somente depois do upload bem-sucedido; respostas no contrato do Lovable (`complementos` com `tipo` `'cliente'`/`'equipe'`, `arquivo_url`, `arquivo_nome`, ordem cronológica); detalhe do chamado inclui o anexo de abertura de `evidencias_protocolos`; CORS restrito; sem retenção.
3. D5: alteração mínima de `admin/documentos-v2` para incluir `complementos` por documento (somente esse acréscimo; o endurecimento geral fica no item 25) e prompt do Lovable para exibi-los no painel.
4. Testes: validador MariaDB do CI (isolamento entre clientes, sessão revogada/expirada, item fechado, limites, auditoria, rollback); testes estáticos dos workflows; teste real pela tela com dois clientes de teste.

**Escopo — fora.** Item 25 (endurecer os workflows existentes de chamados/documentos); abas Certidões/Livros/Obrigações e Inteligência Fiscal (item 20); notificação por e-mail de complementos.

**Riscos.** Upload grande em base64 via proxy pode estourar limite da Edge Function — por isso D3 depende da verificação técnica. Falha entre o upload no Drive e a gravação no banco deixa arquivo órfão no Drive (sem registro): aceitável, registrado; o inverso (registro sem arquivo) não pode acontecer.

---

## 2. Decisões do usuário

### [2026-10-04] Usuário
- "aprovo D1–D5". D3 sem tamanho informado: vale a proposta de 10 MB, limitada ao menor limite técnico do caminho (Edge Function e n8n), que o Codex verifica e registra.
- Observação do usuário para o desenho: o Sistema B vai consumir as informações do Sistema A para a contabilização, com a organização: (1) caixa de entrada; (2) documentos para contabilizar (despesas, contratos, outros); (3) fiscal (NF-e, NFS-e, cupom fiscal, CT-e); (4) financeiro (OFX, PDF, CSV de extratos); (5) contábil (validação e aprovação, com correção de contas e históricos); (6) relatórios contábeis. Tratado em pesquisa de arquitetura separada (ver QUADRO); a T-0008 não define categorias de documento e não deve fixar nada que impeça essa organização — os complementos ficam ligados ao documento/chamado por id, sem classificação nova.

---

## 3. Implementação (Codex)

(aguardando "execute a tarefa T-0008")

### [2026-10-05] Codex — Implementação

**Resultado.** Implementei os artefatos aprovados sem executar nada contra banco,
n8n, Drive, Supabase ou Lovable reais. A migration externa 006 cria o histórico
append-only de complementos de documento, acrescenta o nome do anexo às
mensagens de chamado e expõe quatro procedures `SQL SECURITY INVOKER`. Sessão,
ownership, estado fechado e entrada são revalidados; inserção, `atualizado_em` e
auditoria mínima ficam na mesma transação. Recurso ausente e cross-client têm o
mesmo resultado `not_found`.

Os quatro workflows importáveis estão inativos, sem credenciais e sem retenção.
O token vem somente de `Authorization`; as chamadas SQL usam parâmetros; o
arquivo é validado por tamanho, MIME, extensão e assinatura antes de Drive/banco;
o upload usa uma das cinco subpastas aprovadas dentro da raiz retornada para o
cliente da sessão. A procedure de gravação só é chamada depois do upload. O
detalhe devolve complementos cronológicos e o chamado inclui anexos de abertura.

**Arquivos criados.** Em
`docs/integration/system_a_portal_detalhes/`:

- `006_up.sql`, `006_down.sql`, `verify_006.sql` e
  `test_base_schema.sql`;
- `n8n_portal_detalhe_chamado.json`;
- `n8n_portal_complementar_chamado.json`;
- `n8n_portal_detalhe_documento.json`;
- `n8n_portal_complementar_documento.json`;
- `ADMIN_DOCUMENTOS_V2_PATCH.md`;
- `LOVABLE_PROMPT.md`.

Também foram criados:

- `docs/integration/SYSTEM_A_PORTAL_DETAILS_RUNBOOK.md`;
- `scripts/validate_system_a_portal_details.sh`;
- `tests/unit/test_system_a_portal_details_assets.py`.

**Arquivos alterados.** `.github/workflows/ci.yml` chama o novo validador
MariaDB; `docs/colaboracao/QUADRO.md` encaminha a tarefa para revisão; este
arquivo recebeu somente esta entrada append-only. `.claude/settings.local.json`
já estava não rastreado e foi preservado sem leitura ou alteração.

**Decisões técnicas.** O vínculo `(documento_id, cliente_id)` possui FK composta,
impedindo referência cross-client também no banco. O downgrade falha fechado se
removeria complementos ou nomes novos de anexo; auditoria permanece histórica.
O export original do workflow multi-endpoint `admin/documentos-v2` não está no
Git. Em vez de inventar um workflow completo e possivelmente remover rotas, foi
entregue um patch SQL mínimo e revisável para o `SELECT` existente; o runbook
exige comparar o export antes/depois.

**D3 — limite verificado.** A documentação oficial do n8n vigente em 05/10/2026
informa 16 MiB como limite padrão de webhook. Um arquivo de 10 MiB ocupa cerca
de 13,34 MiB em base64, antes do pequeno envelope JSON, portanto permanece sob
esse teto. A documentação oficial atual das Supabase Edge Functions não publica
limite de corpo e informa 256 MB de memória. Mantive os 10 MiB aprovados e
registrei teste obrigatório pelo proxy real; se a configuração do projeto for
menor, frontend e workflow devem ser reduzidos juntos.

**Testes executados.** Teste específico da T-0008: **11 passed**, incluindo
compilação de todos os nós Code com Node.js. Suíte completa: **657 passed, 20
skipped**, com dois avisos preexistentes de depreciação FastAPI/Starlette. Sintaxe
do shell pelo Git Bash: aprovada. `git diff --check`: aprovado. Varredura de
segredos: `SECRET_SCANNER_CANARY_DETECTION: PASS` e
`RELEASE_SECRET_SCAN: PASS`.

**Não executado.** O validador MariaDB descartável não rodou localmente porque o
Docker Desktop está parado; o CI deve emitir
`PORTAL_DETAILS_MIGRATION_006=VALID`,
`PORTAL_DETAILS_ISOLATION_TESTS=PASS`,
`PORTAL_DETAILS_AUDIT_ATOMICITY=PASS` e
`PORTAL_DETAILS_ROLLBACK=PASS`. A UAT real com dois clientes sintéticos também é
ação do usuário depois da revisão, seguindo o runbook.

**Pendências para revisão/publicação.** Claude deve revisar o diff real e o
resultado do CI. Depois do aceite: backup e preflight; aplicação da 006;
importação/reassociação de credenciais dos quatro workflows; patch mínimo do
workflow administrativo a partir do export real; prompt do Lovable; conferência
das quatro opções de retenção; e UAT com dois clientes. Nenhuma migration
Alembic foi criada — a única migration é a 006 do Sistema A.

## 4. Revisões (Claude) e respostas (Codex)

### [2026-10-05] Claude — Revisão 1

**Veredito: AJUSTES.** São dois ajustes pequenos. O restante está aceito tecnicamente; o aceite final também depende do validador MariaDB no CI.

**O que conferi no diff real:**
- `006_up.sql`:
  - a sessão é revalidada, viva e não revogada, com a collation da coluna;
  - o cliente vem sempre da sessão, e o cliente cruzado recebe `not_found`;
  - a FK composta `(documento_id, cliente_id)` impede referência cruzada;
  - inserção, `atualizado_em` e auditoria (sem token) ficam na mesma transação, com rollback no erro;
  - os complementos são append-only.
- Os quatro workflows:
  - token só do `Authorization`;
  - SQL por `queryReplacement`;
  - arquivo validado por tamanho, MIME, extensão e assinatura antes do Drive;
  - **o estado fechado é conferido antes do upload**, o que evita arquivo órfão nesse caso;
  - a pasta de destino é a do cliente da sessão;
  - `drive_folder_id` é removido da resposta ao portal;
  - retenção `none`, inativos, sem credenciais.
- Testes: `tests/unit/test_system_a_portal_details_assets.py` com 11 testes aprovados (reexecutado).

**Ajustes:**

1. **Cabeçalhos repetidos nas respostas.** Os nós `respondToWebhook` dos quatro workflows repetem `Access-Control-Allow-Methods`, `Access-Control-Allow-Headers` e `Vary` (de 4 a 28 ocorrências por arquivo).
   - Correção: cada cabeçalho uma única vez por nó.
   - Acrescentar um teste que falhe com nome de cabeçalho duplicado num mesmo nó.
2. **Rótulos de status "fechado" sem conferência com a produção.**
   - Os valores usados nas procedures e no nó "Recurso aberto?" foram presumidos:
     - `concluido`/`concluído` para chamados;
     - `processado`/`concluido`/`concluído`/`rejeitado` para documentos.
   - Se a produção usar outro rótulo (ex.: "Resolvido", "Finalizado", "Cancelado"), o cliente complementará item encerrado.
   - Correção: incluir no runbook, antes da aplicação da 006, a consulta somente leitura `SELECT status, COUNT(*) FROM tickets_master GROUP BY status;` e a equivalente em `inbox_documentos`.
   - Incluir também a instrução de parar e reportar se aparecer rótulo fora da lista. O ajuste da lista vira decisão registrada, nunca suposição.

**Observação, sem bloquear:** o patch de `admin/documentos-v2` expõe os complementos a qualquer sessão de funcionário, porque o workflow não exige a permissão do módulo e lista todos os clientes. Isso já está coberto pelo item 25 da fila, que passa a ter prioridade maior depois da publicação desta tarefa.

### [2026-10-05] Codex — Resposta à Revisão 1

Os dois ajustes foram atendidos sem mudar a migration 006, as procedures, o
contrato HTTP ou a ordem de efeitos dos workflows.

1. **Cabeçalhos repetidos:** os cabeçalhos de cada nó `respondToWebhook` foram
   deduplicados preservando a primeira ocorrência. Todos os nós dos quatro
   workflows agora possuem exatamente uma ocorrência de cada nome:
   `Access-Control-Allow-Origin`, `Access-Control-Allow-Methods`,
   `Access-Control-Allow-Headers` e `Vary`. Foi acrescentado um teste que percorre
   todos os nós de resposta e falha com nomes repetidos sem distinguir caixa.
2. **Inventário dos status:** o preflight do runbook agora exige, antes da 006,
   as consultas somente leitura `SELECT status, COUNT(*) ... GROUP BY status`
   para `tickets_master` e `inbox_documentos`. O documento registra as listas
   terminais implementadas e manda parar e reportar rótulo terminal fora delas
   ou qualquer rótulo cuja natureza ativa/terminal não possa ser confirmada. A
   lista só pode mudar por decisão registrada, sincronizada em procedures,
   workflows e testes.

**Arquivos alterados nesta rodada.** Os quatro
`docs/integration/system_a_portal_detalhes/n8n_*.json`,
`docs/integration/SYSTEM_A_PORTAL_DETAILS_RUNBOOK.md`,
`tests/unit/test_system_a_portal_details_assets.py`,
`docs/colaboracao/QUADRO.md` e este registro append-only. Nenhum arquivo ou
migration foi criado; `.claude/settings.local.json` permaneceu intocado.

**Validação.** Testes específicos da T-0008: **12 passed**. Suíte completa:
**658 passed, 20 skipped**, com os mesmos dois avisos preexistentes de
depreciação FastAPI/Starlette. Varredura de segredos:
`SECRET_SCANNER_CANARY_DETECTION: PASS` e `RELEASE_SECRET_SCAN: PASS`.
`git diff --check`: aprovado.

**Pendente.** O validador MariaDB descartável continua dependente do CI porque
o Docker Desktop local está parado. A tarefa retorna ao Claude para nova revisão;
publicação e UAT real continuam fora desta execução.

### [2026-10-05] Claude — Revisão 2

**Veredito: ACEITA tecnicamente.** Resta uma condição: o validador MariaDB do CI (`PORTAL_DETAILS_*=PASS`) precisa passar depois do push.

**Ajustes da revisão 1, conferidos no diff:**
- Nenhum cabeçalho repetido nos quatro workflows (contagem por nó = 1).
- O runbook inclui o inventário `GROUP BY status` antes da 006, com instrução de parar diante de rótulo não previsto.

**Correção feita pelo Claude:** `test_embedded_n8n_code_nodes_compile_in_node` falhava de forma intermitente no Windows (`OSError: [WinError 6]` ao duplicar o stdin herdado pelo `subprocess`). A causa é o ambiente, não o código entregue. Uma linha (`stdin=subprocess.DEVNULL`) estabilizou o teste: 6 de 6 execuções aprovadas, contra 3 falhas em 5 antes.

**Próximo passo:** publicação guiada, conforme `docs/integration/SYSTEM_A_PORTAL_DETAILS_RUNBOOK.md`.

### [2026-10-05] Publicação — inventário de status (preflight)

Produção, consulta somente leitura:
- `tickets_master`: Aberto (6), Em Andamento (1);
- `inbox_documentos`: Novo (14), Recebido (11).

Nenhum rótulo terminal está em uso hoje. Ainda falta confirmar quais rótulos terminais as telas do painel gravam, porque a lista implementada só funciona se eles coincidirem.

### [2026-10-05] Publicação — migration 006 aplicada

- Preflight:
  - colunas e collations conferidas (`token_hash` em `utf8mb4_uca1400_ai_ci`; `inbox_documentos.id`/`cliente_id` int(11), compatíveis com a FK);
  - as colunas de `tickets_master` lidas pela procedure existem;
  - grants: ALL no schema.
- Rótulos de status: chamado terminal "Concluído", confirmado em `listas_opcoes`. Documento: rótulo terminal ainda sem confirmação; não há documento encerrado hoje.
- `006_up.sql` importado pelo proprietário. A conferência confirmou:
  - coluna `tickets_mensagens.anexo_nome`;
  - tabela `inbox_documentos_complementos` com 9 colunas, PK, FK composta e os dois CHECKs;
  - as quatro procedures `INVOKER`.
- Observação: o `verify_006.sql` usa `DATABASE()`, que voltou vazio no phpMyAdmin quando os comandos rodaram em bloco. A conferência foi refeita com o nome do schema literal.

### [2026-10-05] Publicação — patch do painel (D5)

O proprietário enviou o export de produção de "API - Admin - Listagens Gerais V2 (Corrigido)". O baseline está em `docs/integration/system_a_portal_detalhes/baseline/n8n_admin_listagens_gerais_v2.json`.

O Claude gerou `n8n_admin_listagens_gerais_v2_t0008.json` com duas mudanças funcionais:
1. a consulta "Buscar Todos os Documentos" ganha a coluna `complementos`, com `x.cliente_id = d.cliente_id`;
2. o novo nó "Converter Complementos" transforma o texto JSON em lista.

O arquivo é importado inativo e sem gravação de execuções. O teste `test_admin_documentos_patch_changes_only_documents_branch` garante que nenhum outro nó mudou.

Os defeitos preexistentes desse workflow continuam no item 25 da fila: SQL interpolado, `NOW()`, CORS `*`, sem permissão de módulo.

### [2026-10-05] Publicação — Lovable (antes de publicar)

O Lovable aplicou o prompt nos arquivos:
- `src/lib/complemento.ts` e `src/test/complemento.test.ts` (9 testes novos; 30 no total, todos aprovados);
- `TicketDetailDrawer.tsx`, `DocumentDetailDrawer.tsx` e `AdminDocumentos.tsx`, este com linha do tempo somente leitura.

O Lovable também respondeu às duas pendências:
1. o painel não grava status de documento. A única lista é o filtro do portal: Recebido, Em Análise, Processado e Rejeitado. Os rótulos terminais Processado e Rejeitado coincidem com a lista implementada, o que encerra a pendência;
2. o `proxy-webhook` não tem limite próprio de corpo. O teste de 10 MiB pelo caminho real continua obrigatório na UAT.

Os erros 401, 404, 409, 422 e o item fechado ainda não foram testados na tela; serão verificados na UAT.
