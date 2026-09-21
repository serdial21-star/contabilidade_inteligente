# 🔍 PROMPT DE DIAGNÓSTICO COMPLETO — Serdial21
## Análise de Banco de Dados (MySQL) + Aplicativo (React/n8n)

**Data de referência:** 2026-03-19  
**Objetivo:** Identificar TODAS as inconsistências, lacunas e correções necessárias entre o banco de dados MySQL, os workflows n8n e o frontend React para garantir integridade operacional total.

---

## 📋 CONTEXTO DO PROJETO

### Arquitetura
```
Portal do Cliente (React/Vite) ──→ Supabase Edge Functions (proxy) ──→ n8n Webhooks ──→ MySQL (Hostinger)
Painel Administrativo (React/Vite) ──→ fetch direto com Bearer Token ──→ n8n Webhooks ──→ MySQL (Hostinger)
```

### Tecnologias
- **Frontend:** React 18 + TypeScript + Vite + Tailwind CSS + Shadcn/UI
- **Backend:** MySQL (Hostinger) + n8n (middleware de APIs/webhooks)
- **Proxy:** Supabase Edge Functions (`proxy-webhook`, `proxy-file-upload`, `ai-analyst`)
- **Storage:** Supabase Storage (bucket: `client-logos`)
- **Autenticação:** JWT via n8n (admin: `admin_auth_token`, cliente: `auth_token`)

---

## 📊 ESTRUTURA ATUAL DO BANCO DE DADOS (MySQL)

### Tabelas existentes (18 confirmadas):
| # | Tabela | Propósito |
|---|--------|-----------|
| 1 | `clientes` | Cadastro de clientes do escritório |
| 2 | `funcionarios` | Cadastro de funcionários/operadores |
| 3 | `security_credenciais` | Credenciais de acesso (login) |
| 4 | `tickets_master` | Tickets/chamados de clientes |
| 5 | `entregas_master` | Entregas contábeis agendadas |
| 6 | `catalogo_obrigacoes` | Catálogo de obrigações fiscais/contábeis |
| 7 | `impostos_obrigacoes` | Controle de impostos e obrigações por cliente |
| 8 | `inbox_documentos` | Documentos recebidos dos clientes |
| 9 | `evidencias_protocolos` | Evidências e protocolos de processos |
| 10 | `logs_auditoria` | Log de todas as ações do sistema |
| 11 | `listas_opcoes` | Opções dinâmicas para selects (áreas, status, etc.) |
| 12 | `honorarios_contratos` | Contratos de honorários por cliente |
| 13 | `honorarios_parcelas` | Parcelas/faturas mensais de honorários |
| 14 | `honorarios_servicos_avulsos` | Serviços esporádicos faturados |
| 15 | `honorarios_recibos_sequencia` | Controle de numeração de recibos |
| 16 | `permissoes_funcionario_modulos` | RBAC: acesso CRUD por módulo/funcionário |
| 17 | `permissoes_funcionario_clientes` | Restrição de acesso a clientes por funcionário |
| 18 | `permissoes_cliente_portal` | Visibilidade de módulos no portal do cliente |

### Tabelas PLANEJADAS (ainda não confirmadas se foram criadas):
| # | Tabela | Módulo | Status esperado |
|---|--------|--------|-----------------|
| 19 | `certidoes_tipos` | CND | Catálogo de tipos de certidões |
| 20 | `certidoes_clientes` | CND | Certidões emitidas por cliente |
| 21 | `livros_tipos` | Livros Contábeis | Catálogo de tipos de livros |
| 22 | `livros_clientes` | Livros Contábeis | Livros gerados por cliente |
| 23 | `obrigacoes_acessorias_tipos` | SPED/Declarações | Catálogo de obrigações acessórias |
| 24 | `obrigacoes_acessorias_clientes` | SPED/Declarações | Obrigações por cliente |
| 25 | `tarefas_internas` | Central de Operações | Tarefas criadas manualmente pela equipe |

---

## 🔌 ENDPOINTS n8n — MAPEAMENTO COMPLETO

### Central de Operações (Kanban Unificado)
| Endpoint | Método | Uso atual no frontend |
|----------|--------|-----------------------|
| `/admin-kanban-v3` | GET | Listar todos os itens (ticket+entrega+obrigação+tarefa) |
| `/admin-create-item-v3` | POST | Criar item (tipo_item + campos variáveis) |
| `/admin-update-item-v1` | POST | Atualizar item (envia id_origem + tipo_item) |
| `/admin-delete-item-v3` | POST | Excluir item (envia tipo_item + id_origem) |
| `/admin-dashboard-v2` | GET | KPIs: total, atrasadas, vence_hoje, próximos_5_dias, etc. |
| `/admin-agenda-v2` | GET | Itens com data para calendário (usado em /admin/agenda separado) |
| `/admin-clientes-options-v1` | GET | Select dinâmico de clientes (id + nome_cliente) |
| `/admin-funcionarios-options-v1` | GET | Select dinâmico de funcionários (id + nome_funcionario) |

### Tickets
| Endpoint | Método | Uso |
|----------|--------|-----|
| `/admin/tickets` | GET/POST | CRUD completo de tickets |
| `/admin/responder-ticket-v2` | POST | Responder ticket + atualizar status |

### Outros módulos
| Endpoint | Método | Uso |
|----------|--------|-----|
| `/admin/clientes-v2` | POST | CRUD de clientes |
| `/admin/entregas` | POST | CRUD de entregas |
| `/admin/funcionarios` | POST | Listar/CRUD funcionários |
| `/admin/login-v2` | POST | Login admin |
| `/admin/permissoes/funcionario` | POST | Consultar/salvar permissões |
| `/admin/permissoes/cliente` | POST | Consultar/salvar permissões do portal |
| `/admin/honorarios-v2` | POST | CRUD de contratos e parcelas |
| `/admin/honorarios-parcelas-v2` | POST | Listar/atualizar parcelas |
| `/admin/honorarios-servicos-v2` | POST | CRUD de serviços avulsos |
| `/admin/fiscal` | POST | Dados fiscais (NF-e) |
| `/admin/impostos-v2` | POST | Guias de impostos |

### Portal do Cliente
| Endpoint | Método | Uso |
|----------|--------|-----|
| `/portal-serdial-v2` | POST | Login cliente |
| `/cliente/honorarios-v2` | POST | Faturas do cliente |
| `/cliente/certidoes-v2` | GET | Certidões do cliente |
| `/cliente/livros-v2` | GET | Livros contábeis |
| `/cliente/obrigacoes-v2` | GET | Obrigações acessórias |

---

## 🖥️ MÓDULOS DO FRONTEND — ESTADO ATUAL

### Painel Administrativo (/admin/*)
| Rota | Módulo | Status |
|------|--------|--------|
| `/admin` | Central de Operações (Kanban+Agenda+Lista) | ✅ Implementado, unificado |
| `/admin/clientes` | Gestão de Clientes | ✅ Implementado |
| `/admin/tickets` | Gestão de Tickets | ✅ Implementado (Kanban+Tabela+Drawer) |
| `/admin/entregas` | Controle de Entregas | ✅ Implementado |
| `/admin/documentos` | Gestão de Documentos | ✅ Implementado |
| `/admin/impostos` | Guias de Impostos | ✅ Implementado |
| `/admin/honorarios` | Faturamento e Honorários | ✅ Implementado |
| `/admin/ferramentas-ia` | Ferramentas de IA (Analyst+Extrator) | ✅ Implementado |
| `/admin/atalhos` | Atalhos Rápidos | ✅ Implementado |
| `/admin/equipe` | Gestão de Equipe + Permissões | ✅ Implementado |
| `/admin/configuracoes` | Configurações (listas dinâmicas) | ✅ Implementado |
| `/admin/tarefas` | Redireciona para /admin | ✅ Consolidado |
| `/admin/agenda` | Agenda separada (usa API própria) | ✅ Implementado |

### Portal do Cliente (/*)
| Rota | Módulo | Status |
|------|--------|--------|
| `/login` | Login do cliente | ✅ Implementado |
| `/dashboard` | Dashboard resumo | ✅ Implementado |
| `/chamados` | Meus Chamados | ✅ Implementado |
| `/documentos` | Enviar Documentos | ✅ Implementado |
| `/biblioteca` | Biblioteca de Entregas | ✅ Implementado |
| `/meus-documentos` | Meus Documentos (certidões, livros) | ✅ Implementado |
| `/honorarios` | Meus Honorários | ✅ Implementado |
| `/impostos` | Guias de Impostos | ✅ Implementado |

---

## ⚠️ PONTOS DE ATENÇÃO IDENTIFICADOS NO FRONTEND

### 1. Central de Operações — Dados e Filtros
- **Dados unificados:** Kanban, Lista e Agenda agora usam a MESMA base de dados (`/admin-kanban-v3`). A Agenda antiga (`/admin-agenda-v2`) ainda é usada em `/admin/agenda` separadamente.
- **Filtros implementados:** busca textual (título, cliente, responsável, departamento, tipo_item), filtro por tipo, cliente, departamento, responsável.
- **status_padronizado:** O Kanban usa `item.status_padronizado || item.status` para distribuir nas colunas.
- **id_origem:** Update usa `id_origem` em vez de `id` no payload.

### 2. Formulário de Criação/Edição
- **Ticket:** Label muda para "Assunto", campo Departamento é oculto, Cliente obrigatório, envia `responsavel_nome` (string).
- **Tarefa:** Departamento e Tipo de Tarefa obrigatórios, envia `responsavel_id` (numérico).
- **Obrigação:** Cliente obrigatório.
- **Departamento:** Valores enviados em minúsculo (fiscal, contabil, dp, societario, auditoria).

### 3. Possíveis inconsistências a verificar
- O campo `cliente` vs `cliente_nome` nos retornos da API (documentação diz `cliente`, frontend espera `cliente_nome`).
- A API `/admin-kanban-v3` retorna `status_padronizado`? Ou o frontend precisa inferir?
- A tabela `tarefas_internas` existe no MySQL? Ou tarefas são salvas em outra tabela?
- Os endpoints v1/v2/v3 estão todos ativos e funcionais no n8n?
- O campo `id_origem` é retornado pela API ou precisa ser inferido do `id`?

---

## 🎯 CHECKLIST DE DIAGNÓSTICO — EXECUTE TODAS AS VERIFICAÇÕES

### A) BANCO DE DADOS MYSQL

```
□ A.1 — Listar TODAS as tabelas existentes no banco com: SHOW TABLES;
□ A.2 — Para cada tabela, mostrar estrutura completa: DESCRIBE <tabela>;
□ A.3 — Verificar se tabelas planejadas existem:
         - certidoes_tipos, certidoes_clientes
         - livros_tipos, livros_clientes
         - obrigacoes_acessorias_tipos, obrigacoes_acessorias_clientes
         - tarefas_internas (ou equivalente)
□ A.4 — Verificar integridade referencial (FOREIGN KEYS):
         - Todas as FK apontam para tabelas existentes?
         - ON DELETE CASCADE está correto em todas?
□ A.5 — Verificar índices e UNIQUE KEYS para evitar duplicação em automações
□ A.6 — Verificar se campos de data possuem DEFAULT adequados
□ A.7 — Verificar se ENUMs cobrem todos os valores usados pelo frontend:
         - status de tickets: novo, em_andamento, aguardando_cliente, concluido
         - status padronizado: a_fazer, em_andamento, aguardando_cliente, em_conferencia, concluido, atrasado
         - tipo_item: ticket, entrega, obrigacao, tarefa
         - prioridade: alta, media, baixa
         - departamento: fiscal, contabil, dp, societario, auditoria
         - tipo_tarefa: rotina, pontual, correcao, consultoria
         - forma_pagamento: boleto, pix, transferencia, debito_automatico
□ A.8 — Verificar tabela logs_auditoria: está sendo populada?
□ A.9 — Verificar tabela listas_opcoes: tem dados para todos os selects dinâmicos?
□ A.10 — Verificar se honorarios_recibos_sequencia tem registro para o ano corrente (2026)
```

### B) WORKFLOWS n8n — ENDPOINTS

```
□ B.1 — Listar TODOS os workflows ativos no n8n
□ B.2 — Para cada endpoint listado acima, verificar:
         - O webhook existe e está ativo?
         - Suporta requisições OPTIONS (CORS)?
         - Retorna headers: Access-Control-Allow-Origin: *, Access-Control-Allow-Methods, Access-Control-Allow-Headers
□ B.3 — Verificar resposta do GET /admin-kanban-v3:
         - Retorna array de itens com TODOS os campos esperados?
         - Inclui: id, id_origem, titulo, descricao, tipo_item, cliente_nome, cliente_id, departamento, status, status_padronizado, prioridade, data_referencia, data_vencimento, responsavel_id, responsavel_nome, tags, created_at, competencia, tipo_tarefa
         - Tickets aparecem neste endpoint?
         - Entregas aparecem neste endpoint?
         - Obrigações aparecem neste endpoint?
□ B.4 — Verificar POST /admin-create-item-v3:
         - Aceita payload com: titulo, descricao, tipo_item, departamento, tipo_tarefa, prioridade, data_vencimento, competencia, responsavel_id, responsavel_nome, cliente_id, tags
         - Grava na tabela correta baseado em tipo_item
         - Retorna { success: true, message: "..." }
□ B.5 — Verificar POST /admin-update-item-v1:
         - Aceita payload com: id_origem, tipo_item, + campos editáveis
         - Atualiza na tabela correta baseado em tipo_item
         - Retorna { success: true, message: "..." }
□ B.6 — Verificar POST /admin-delete-item-v3:
         - Aceita payload com: { tipo_item, id_origem }
         - Realiza soft-delete ou hard-delete?
         - Retorna { success: true, message: "..." }
□ B.7 — Verificar GET /admin-clientes-options-v1:
         - Retorna array com { id, nome_cliente }
         - Filtrado por clientes ativos?
□ B.8 — Verificar GET /admin-funcionarios-options-v1:
         - Retorna array com { id, nome_funcionario }
         - Filtrado por funcionários ativos?
□ B.9 — Verificar GET /admin-dashboard-v2:
         - Retorna counters: total_operacoes, atrasadas, vence_hoje, proximos_5_dias, aguardando_cliente, concluidas
□ B.10 — Verificar GET /admin-agenda-v2:
          - Retorna itens com: id, titulo, tipo_item, cliente_nome, data_vencimento, data_evento, status, prioridade, responsavel_nome, departamento
□ B.11 — Verificar se TODOS os endpoints retornam 401 para token inválido/expirado
□ B.12 — Verificar se automações CRON estão ativas:
          - Geração mensal de parcelas (Dia 1, 00:05)
          - Marcação de inadimplência (Diário, 06:00)
          - Renovação de certidões (Dia 1, 01:00)
          - Geração de obrigações acessórias (Dia 1, 02:00)
          - Alerta de prazos (Diário, 08:00)
```

### C) FRONTEND REACT — CONSISTÊNCIA

```
□ C.1 — Central de Operações (/admin):
         - Kanban distribui itens por status_padronizado?
         - Todos os tipos de item (ticket, entrega, obrigação, tarefa) aparecem?
         - Filtro de cliente carrega dados da API?
         - Filtro de responsável carrega dados da API?
         - Busca textual funciona (título, cliente, responsável)?
         - Criar item funciona para todos os tipos?
         - Editar item abre com dados preenchidos?
         - Excluir item funciona com confirmação?
         - Após CRUD, tela atualiza automaticamente?

□ C.2 — Tickets (/admin/tickets):
         - Tickets criados aqui aparecem na Central de Operações?
         - Status do ticket no Kanban da Central é mapeado corretamente?
         - Drawer de detalhes abre com histórico de chat?

□ C.3 — Honorários (/admin/honorarios):
         - Dashboard cards exibem dados reais?
         - Parcelas são geradas automaticamente pelo CRON?
         - Serviços avulsos funcionam separadamente?

□ C.4 — Portal do Cliente:
         - Login gera token e armazena corretamente?
         - Permissões do portal (permissoes_cliente_portal) são respeitadas?
         - Módulos ocultos não aparecem na sidebar?

□ C.5 — Permissões (RBAC):
         - AdminRouteGuard verifica permissão antes de renderizar?
         - Administrador/Admin tem bypass total?
         - Funcionário sem permissão é bloqueado?
         - Permissões de acesso a clientes são respeitadas nos filtros?

□ C.6 — Meus Documentos (/meus-documentos):
         - Aba de Certidões carrega dados?
         - Aba de Livros Contábeis carrega dados?
         - Aba de Obrigações carrega dados?
         - Ou essas abas estão vazias/mockadas?
```

### D) AUTOMAÇÕES E INTEGRIDADE

```
□ D.1 — Parcelas de honorários:
         - São geradas automaticamente no dia 1?
         - Parcelas atrasadas são marcadas automaticamente?
         - Não há duplicação (UNIQUE KEY uk_contrato_competencia)?

□ D.2 — Certidões negativas:
         - São renovadas automaticamente no dia 1?
         - Certidões antigas são marcadas como "substituída"?
         - Não há duplicação (UNIQUE KEY uk_cliente_tipo_competencia)?

□ D.3 — Obrigações acessórias:
         - São geradas automaticamente no dia 1?
         - Obrigações atrasadas são marcadas automaticamente?
         - Prazos legais são calculados corretamente?

□ D.4 — Logs de auditoria:
         - Todas as ações de escrita geram log?
         - Estrutura do log: acao, detalhes (JSON), usuario_id, criado_em?
```

---

## 📤 FORMATO DE RESPOSTA ESPERADO

Para cada item verificado, responda no formato:

```
### [Código] — [Descrição]
- **Status:** ✅ OK | ⚠️ Atenção | ❌ Erro
- **Detalhe:** [O que foi encontrado]
- **Correção sugerida:** [Se aplicável, SQL ou configuração necessária]
- **Prioridade:** 🔴 Crítica | 🟡 Média | 🟢 Baixa
```

### Ao final, consolidar:
1. **Tabela resumo** com todos os erros encontrados, ordenados por prioridade
2. **Scripts SQL** prontos para execução (CREATE, ALTER, INSERT, UPDATE)
3. **Configurações n8n** que precisam ser ajustadas
4. **Alterações no frontend** que precisam ser feitas
5. **Automações CRON** que precisam ser criadas ou corrigidas

---

## 🔐 CREDENCIAIS PARA TESTE

> ⚠️ Preencha com as credenciais reais antes de enviar para análise:

- **MySQL Host:** [host da Hostinger]
- **MySQL Database:** [nome do banco]
- **MySQL User:** [usuário]
- **n8n URL base:** https://n8n.serdial21.com
- **Admin token de teste:** [gerar um token válido para testes]

---

## 📝 NOTAS IMPORTANTES

1. O frontend NUNCA acessa MySQL diretamente — sempre via n8n webhooks
2. O proxy Supabase (`proxy-webhook`) é usado apenas pelo Portal do Cliente
3. O Painel Admin faz chamadas diretas aos webhooks n8n com Bearer Token
4. Respostas devem seguir padrão: `{ success: true/false, data: [...], message: "..." }`
5. Todo erro 401 deve redirecionar para a tela de login correspondente
6. CORS é obrigatório em todos os webhooks n8n
7. Departamentos devem ser enviados em minúsculo: fiscal, contabil, dp, societario, auditoria
