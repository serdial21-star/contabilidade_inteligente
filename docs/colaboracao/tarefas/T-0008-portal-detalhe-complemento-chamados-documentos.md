# T-0008 — Portal do cliente: detalhe e complemento de chamados e documentos

| Campo | Valor |
|---|---|
| Estado | DIAGNÓSTICO — aguardando informações do usuário |
| Origem | QUADRO, fila item 20 (primeira parte); escolhida pelo usuário em 04/10/2026 para destravar os testes práticos com clientes |
| Sistema | Sistema A (n8n, MySQL, frontend Lovable) |
| Exige ADR | a definir após o diagnóstico (depende de haver ou não estrutura de dados para mensagens/complementos) |
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
