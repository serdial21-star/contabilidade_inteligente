# ADR 0018 — Autorização por permissão nas operações administrativas de clientes do Sistema A

## Status

**Aceita** por decisão explícita do usuário em 2026-10-01 (proposta no mesmo dia). D1 e D2 decididos conforme recomendado; diagnóstico da seção "Pré-condições" concluído: os 7 funcionários ativos já têm `clientes.visualizar`, `criar` e `editar`, portanto ninguém é bloqueado na publicação. Tarefa de execução: `docs/colaboracao/tarefas/T-0003-permissao-operacoes-clientes-sistema-a.md`.

Complementa o pacote de cadastro seguro de clientes (`docs/integration/SYSTEM_A_CLIENT_MANAGEMENT_RUNBOOK.md`, liberado em 30/09/2026) e a correção de permissões de 22/09/2026 (`docs/integration/SYSTEM_A_SECURITY_GAPS.md`, SG-03 e SG-19). Não altera a ponte A→B (ADR 0014) nem autoriza sincronização entre os sistemas.

## Contexto

As três operações administrativas de clientes do Sistema A autenticam o funcionário, mas não o autorizam:

- `GET /admin/clientes-v2` (workflow `n8n_admin_client_list_v2.json`, consulta inline);
- `POST /admin/novo-cliente-v2` (`sp_admin_cliente_create`, `001_up.sql:149-171`);
- `POST /admin/editar-cliente-v2` (`sp_admin_cliente_update`, `002_up.sql:98-120`).

A única condição é sessão válida, não revogada, de funcionário com `status = 'Ativo'`. Nenhuma consulta usa `funcionarios.cargo` nem `permissoes_funcionario_modulos`. Os webhooks são públicos; o controle da tela no frontend é decorativo e, na cópia local do código, fail-open (`usePermissoes.ts:94-104`, `useCanAccess.ts:13-16`).

Consequência demonstrada na auditoria de 01/10/2026 (achado #3): um funcionário com cargo `Auditor` — que pela política do próprio Sistema A só visualiza — pode chamar `editar-cliente-v2` com o próprio token e trocar o e-mail de qualquer cliente. Em seguida, a recuperação de senha do portal entrega o link ao novo e-mail, e a conta do cliente é tomada. A troca de e-mail não revoga as sessões do cliente nem os links pendentes, e a auditoria (`002_up.sql:235-246`) registra só a mudança de status.

Fatos verificados:

- `permissoes_funcionario_modulos` existe no banco de produção (schema exportado em 22/09/2026, `SYSTEM_A_RUNTIME_VERIFICATION.md:206`).
- Modelo previsto pelo próprio Sistema A (`PROMPT_PERMISSOES_N8N_MYSQL.md`, na cópia local do código): módulo `clientes`; ações `visualizar`, `criar`, `editar`, `excluir`; coluna `permitido`; chave única `(funcionario_id, modulo, acao)`; middleware de backend **fail-closed** (sem linha ou `permitido = 0` → negar), com o mapeamento listar → `visualizar`, criar → `criar`, editar → `editar`.
- Cargos usados no código: `Administrador`, `Admin` (sinônimo), `Operador`, `Auditor`. O frontend trata `Administrador`/`Admin` como acesso total.
- Em 22/09/2026 os workflows de leitura de permissões passaram a negar por padrão (SG-03 resolvido).

Não verificado: se todos os funcionários ativos têm linhas de permissão preenchidas; a estrutura exata da tabela em produção. Ambos são pré-condições desta decisão.

## Decisão proposta

1. **Autorização no banco, no mesmo ponto da autenticação.** Uma rotina única no MySQL resolve o funcionário a partir do token e decide a autorização para `(modulo, acao)`. As procedures de criação e edição e a listagem passam a usá-la. O `funcionario_id` enviado pelo formulário continua ignorado.
2. **Regra de autorização (D1 — recomendação do Claude):** `cargo` lido do banco igual a `Administrador` ou `Admin` → autorizado; qualquer outro cargo → autorizado somente se existir linha `permitido = 1` para `('clientes', ação)`; sem linha → **negado**. Cargo vazio ou desconhecido → negado.
3. **Troca de e-mail ou de documento fiscal (D2 — recomendação do Claude):** exige cargo `Administrador`/`Admin`, mesmo para quem tem `clientes.editar`. Motivo: é o vetor de tomada de conta; a matriz do Sistema A não tem ação própria para isso, e criar uma ação nova seria inventar regra.
4. **Efeitos da troca de e-mail:** na mesma transação, revogar as sessões do cliente e os links de senha pendentes.
5. **Auditoria:** registrar `email_changed` e `document_changed` com SHA-256 dos valores anterior e novo (nunca o valor em claro), além do que já é registrado; registrar também as negações por falta de permissão.
6. **Resposta:** distinguir `unauthorized` (sessão inválida, HTTP 401) de `forbidden` (sessão válida sem permissão, HTTP 403), sem revelar dados do cliente.

## Pré-condições (antes da publicação)

- Diagnóstico somente leitura, executado pelo usuário no phpMyAdmin, com a estrutura da tabela e a contagem de permissões de clientes por funcionário ativo (sem nomes nem e-mails).
- Se algum funcionário que precisa trabalhar com clientes não tiver as linhas, o administrador as concede **pela tela de Permissões do Sistema A antes** de publicar. Este ADR não concede permissões automaticamente.

## Alternativas consideradas

- **Só cargo, sem a matriz:** mais simples, mas ignora a configuração por funcionário que o Sistema A já mantém e contraria a especificação do próprio sistema.
- **Sem linha → padrão do cargo (`fallbackPorCargo`):** mantém o acesso amplo por ausência de configuração (SG-19) e contraria a correção de 22/09/2026.
- **Validar só no n8n:** duplica a regra em três workflows e deixa as procedures chamáveis sem autorização; a regra no banco protege qualquer chamador.
- **Ação nova `alterar_email`:** não existe na matriz do Sistema A; criá-la exige mudar a tela de Permissões, o que é decisão de produto fora desta tarefa.

## Consequências

- Funcionários sem permissão explícita deixam de listar, criar ou editar clientes. Isso é intencional e exige a preparação descrita nas pré-condições.
- O frontend continua mostrando botões conforme a própria lógica; o backend passa a recusar com 403. Ajustar a tela à matriz de permissões é tarefa separada.
- A restrição por cliente (`permissoes_funcionario_clientes`) e a exclusão de clientes continuam fora de escopo.

## Emenda — 2026-10-01 (decisões D3 e D4 do usuário, revisão 1 da T-0003)

- **D3 — ajusta o item 3 da decisão:** preencher o **primeiro** CPF/CNPJ de um cliente que não tinha documento (Lead) é permitido a quem tem `clientes.editar`. Trocar um documento existente continua exigindo `Administrador`/`Admin`. Qualquer alteração de e-mail, inclusive o primeiro, continua exigindo `Administrador`/`Admin`.
- **D4 — substitui o item 5 da decisão:** a auditoria registra que houve troca de e-mail ou de documento (evento, funcionário, data e `request_id`), **sem hash nem valor**. Motivo: SHA-256 sem chave secreta de um CPF é revertido por tentativa em segundos (cerca de 10^9 valores possíveis), portanto o hash não protegia o dado e o mantinha, na prática, na auditoria (LGPD, art. 46; `AGENTS.md` 6.9, minimização). A recuperação após um incidente não depende do valor antigo: o administrador confirma o e-mail correto com o cliente.
- A comparação do cargo passa a ser binária (sem equivalência de acentos), para aceitar somente `Administrador` e `Admin`.

