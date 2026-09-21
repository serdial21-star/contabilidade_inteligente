# Dossiê de Integração — Serdial21 Connect Hub

> Documento destinado a uma IA/equipe que irá desenvolver a integração entre um **programa de contabilidade externo** e a plataforma Serdial21 já existente.
> Versão: setembro/2026. Não contém senhas nem chaves privadas.

---

## 1. O que já existe hoje

A Serdial21 opera uma plataforma web com **dois ambientes** sobre a mesma base de dados:

| Ambiente | Rota de entrada | Usuários |
|---|---|---|
| Portal do Cliente | `/login` | Clientes do escritório |
| Painel Administrativo | `/admin/login` | Equipe interna Serdial21 |

**Arquitetura em 3 camadas:**

```text
Navegador  ──►  Frontend React (Vite, SPA)
                      │  fetch() direto (JSON / FormData)
                      ▼
              n8n self-hosted — https://n8n.serdial21.com/webhook/*
                      │            (camada de API/middleware)
        ┌─────────────┼───────────────┬──────────────┐
        ▼             ▼               ▼              ▼
   MySQL Hostinger  Google Drive   SMTP Hostinger  Z-API (WhatsApp)
   (dados)          (arquivos)     (e-mails)       (mensagens)

   Lateral: Supabase/Lovable Cloud — Edge Functions (proxy-webhook,
   proxy-file-upload, ai-analyst) e Storage (apenas logos de clientes)
```

**Ponto-chave para a integração:** o frontend **não fala com o MySQL**. Toda leitura e escrita passa por **webhooks n8n**. Portanto, o programa de contabilidade externo deve integrar-se **na camada n8n** (ou diretamente no MySQL, com muito cuidado), nunca no React.

---

## 2. Módulos funcionais já entregues

### Portal do Cliente
- Login com token Bearer e recuperação de senha por link mágico
- Dashboard com indicadores (impostos a pagar, chamados abertos, documentos pendentes)
- Chamados/Helpdesk (abertura, timeline, complemento de informações)
- Envio de documentos (drag & drop, múltiplos arquivos, categoria + competência)
- Biblioteca unificada em 5 abas: Entregas, Documentos, Certidões, Livros Contábeis, Obrigações
- Impostos (consulta e fluxo de pagamento com comprovante)
- Honorários (parcelas, vencimentos, recibos)

### Painel Administrativo
- Login próprio, permissões por módulo e por cliente (RBAC)
- Central de Operações (Kanban de tarefas/obrigações/tickets, agenda, KPIs)
- Clientes (cadastro completo, logo, criação de infraestrutura no Drive)
- Equipe/funcionários e gestão de permissões
- Tickets (tabela + kanban, respostas, anexos)
- Impostos e Honorários (lançamento, cobrança, baixa)
- Documentos: inbox de recebidos + envio de arquivos ao cliente
- Ferramentas de IA: extrator fiscal de XML (NF-e), analisador ICMS/CMV, analista de balanço
- Atalhos, lembretes e central de ajuda

---

## 3. Contrato de API atual (camada n8n)

**Base:** `https://n8n.serdial21.com/webhook`
**Formato:** `POST` com `Content-Type: application/json` (uploads usam `multipart/form-data`)
**Autenticação:** header `Authorization: Bearer <token>`
- Cliente: token obtido em `/portal-serdial-v2`, guardado como `auth_token`
- Admin: token obtido em `/admin/login-v2`, guardado como `admin_auth_token`
**Regra de auditoria:** a identidade do usuário é extraída do token no backend — nunca de um `id` enviado no corpo.
**Resposta esperada:** JSON com `success: true` (HTTP 200 sozinho não indica sucesso).
**CORS:** todo webhook precisa responder `OPTIONS` com `Access-Control-Allow-Origin`, `-Headers: Content-Type, Authorization` e `-Methods: GET, POST, OPTIONS`.

### Endpoints em uso pelo frontend

**Autenticação**
`/portal-serdial-v2`, `/portal/me-v2`, `/portal/solicitar-senha`, `/portal/redefinir-senha`,
`/admin/login-v2`, `/admin/solicitar-senha`

**Portal do cliente**
`/portal/meus-chamados-v2`, `/portal/abrir-ticket-v2`, `/portal/detalhe-chamado`, `/portal/complementar-chamado`,
`/portal/meus-documentos-v2`, `/portal/detalhe-documento`, `/portal/complementar-documento`, `/portal/receber-arquivo-v2`,
`/portal/certidoes-v2`, `/portal/livros-contabeis-v2`, `/portal/obrigacoes-v2`,
`/portal/impostos-v2`, `/portal/pagar-imposto-v2`, `/portal/honorarios-v2`

**Administrativo**
`/admin-dashboard-v2`, `/admin-kanban-v3`, `/admin-create-item-v5`, `/admin-update-item-v5`, `/admin-delete-item-v3`, `/admin-agenda-v2`,
`/admin/clientes-v2`, `/admin/novo-cliente-v2`, `/admin/equipe-v2`, `/admin/funcionarios`, `/admin/novo-funcionario`, `/admin/editar-funcionario`,
`/admin/tickets-v2`, `/admin/responder-ticket-v2`,
`/admin/impostos-v2`, `/admin/novo-imposto`, `/admin/honorarios-v2`, `/admin/honorarios-parcelas-v2`,
`/admin/documentos-v2`, `/admin/enviar-inbox`, `/admin/upload-documento-cliente`,
`/admin/permissoes/funcionario`, `/admin/permissoes/funcionario/salvar`, `/admin/permissoes/cliente`, `/admin/permissoes/cliente/salvar`,
`/admin/fiscal/upload-xml`, `/admin/fiscal/listar`, `/admin/fiscal/conferir`,
`/admin-clientes-options-v1`, `/admin-funcionarios-options-v1`, `/admin/atalhos`, `/listar-arquivos`

---

## 4. Domínios de dados (entidades principais no MySQL)

| Domínio | Conteúdo | Chave de ligação |
|---|---|---|
| Clientes | razão social, CNPJ, regime tributário, contatos, logo, pasta Drive | `cliente_id` / CNPJ |
| Funcionários | equipe, cargo, status | `funcionario_id` |
| Permissões | módulo × ação (visualizar/criar/editar/excluir) e acesso por cliente | `funcionario_id` |
| Tickets | chamados, departamento, prioridade, status, histórico | `cliente_id` |
| Documentos | recebidos do cliente e enviados ao cliente; categoria, competência, vencimento, URL do Drive | `cliente_id` |
| Impostos | tipo, competência, vencimento, valor, status, comprovante | `cliente_id` |
| Honorários | contrato, parcelas, vencimento, valor, recibo | `cliente_id` |
| Operações | tarefas, obrigações e tickets no Kanban; responsável, prazo, status | `cliente_id`, `funcionario_id` |

**Convenções de dados obrigatórias:**
- Competência: `YYYY-MM` no banco, exibida como `MM/AAAA`
- Valores monetários: string decimal (`"1234.56"`)
- Categorias e status: slug minúsculo com underline (`notas_fiscais`, `em_andamento`)
- Exclusão lógica (soft delete)
- Documentos ficam no Google Drive; o MySQL guarda apenas metadados + URL

---

## 5. Como integrar o programa de contabilidade

Três caminhos possíveis, do mais recomendado ao menos:

### Opção A — Integração via novos webhooks n8n (recomendada)
O programa contábil chama webhooks dedicados e o n8n cuida de validação, gravação e notificações.

Endpoints sugeridos a criar (prefixo `/contabil/`):
- `POST /contabil/sync-clientes` — o sistema contábil envia ou recebe a carteira de clientes (chave: CNPJ)
- `POST /contabil/lancar-obrigacao` — cria obrigação/tarefa no Kanban a partir do calendário fiscal
- `POST /contabil/publicar-documento` — publica guia, balancete, folha ou livro na Biblioteca do cliente
- `POST /contabil/lancar-imposto` — cria imposto a pagar visível ao cliente
- `GET  /contabil/documentos-recebidos` — lista o que os clientes enviaram (para importação no programa)
- `POST /contabil/baixa-pagamento` — confirma pagamento e anexa comprovante
- `POST /contabil/webhook-eventos` — callback do Serdial21 para o programa (documento enviado, chamado aberto, imposto pago)

Autenticação máquina-a-máquina: header `X-API-Key` fixo por aplicação (não usar o token de usuário) + lista de IPs permitidos.

### Opção B — Banco compartilhado
O programa contábil lê/escreve diretamente no MySQL. Mais rápido, porém sem validação, sem auditoria e com risco de quebrar as telas. Só aceitável para leitura em views dedicadas.

### Opção C — Importação por arquivo
Troca por CSV/XML em pasta do Google Drive, processada por rotina agendada no n8n. Útil como fallback ou para carga inicial.

### Regras que a integração deve respeitar
1. Identificar o cliente sempre por **CNPJ normalizado** (só dígitos) — o `cliente_id` é interno.
2. Toda escrita precisa registrar origem (`origem: "sistema_contabil"`) para auditoria.
3. Responder e consumir sempre JSON com `success` e `message`.
4. Operações devem ser **idempotentes** (chave externa `referencia_externa` única) para evitar duplicidade em reenvios.
5. Documento publicado ao cliente exige: `cliente_cnpj`, `titulo`, `categoria`, `competencia`, `vencimento` (opcional), arquivo.
6. Notificações ao cliente (e-mail/WhatsApp) são disparadas pelo n8n, não pelo programa externo.

---

## 6. Pendências conhecidas (afetam a integração)

| # | Pendência | Impacto |
|---|---|---|
| 1 | Webhook `/admin/upload-documento-cliente` ainda não criado no n8n | Envio de arquivos ao cliente não grava |
| 2 | `/admin-update-item-v5` responde sucesso mas não persiste o novo status | Kanban não fixa o card arrastado |
| 3 | Versionamento misto de endpoints (v1/v2/v3/v5) sem mapa oficial | Risco de chamar rota inexistente |
| 4 | CORS não configurado em todos os webhooks | Erros "Failed to fetch" |
| 5 | Permissões podem retornar vazias | Hoje há fallback permissivo; precisa ser populado no banco |
| 6 | Não há chave de API para sistemas externos | Precisa ser criada antes da integração |

---

## 7. Próximos passos sugeridos

1. Congelar e publicar o **mapa oficial de endpoints** (nome, versão, payload, resposta) — base do contrato.
2. Padronizar CORS e `Respond to Webhook` em todos os workflows n8n.
3. Criar o mecanismo de **API Key** para aplicações externas, com log de chamadas.
4. Definir o **catálogo de eventos** que o Serdial21 enviará ao programa contábil.
5. Implementar os endpoints `/contabil/*` acima, um por vez, começando por `sync-clientes`.
6. Montar ambiente de homologação separado antes de ligar em produção.

---

## 8. Perguntas a responder antes de codar a integração

1. O programa contábil roda local (desktop) ou em servidor com IP fixo?
2. Qual será a fonte de verdade da carteira de clientes: Serdial21 ou o programa contábil?
3. A sincronização será em tempo real (webhook) ou por lote agendado?
4. O programa gera os arquivos (guias, balancetes) ou apenas os dados?
5. Haverá conciliação de pagamentos nos dois sentidos?

