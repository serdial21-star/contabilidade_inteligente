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
