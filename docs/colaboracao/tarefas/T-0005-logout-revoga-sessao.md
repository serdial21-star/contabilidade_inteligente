# T-0005 — "Sair" revoga a sessão no servidor (funcionários e clientes)

| Campo | Valor |
|---|---|
| Estado | CI VERDE — aguardando publicação guiada |
| Origem | QUADRO, fila item 17; teste da T-0003 em 03/10/2026; dossiê `docs/integration-input/DOSSIE_SERDIAL21.md` itens 13 e P1-8 |
| Sistema | Sistema A (artefatos versionados em `docs/integration/`) |
| Exige ADR | não — aplica padrão já aceito (procedures `INVOKER` + workflow fino, ADR 0018); decisões D1–D4 registradas aqui |
| Exige ação do usuário | sim — migration no phpMyAdmin, importar workflows no n8n, aplicar prompt no Lovable |

---

## 1. Briefing (Claude)

### [2026-10-03] Claude — Briefing

**Problema.** O "Sair" do painel administrativo apenas limpa o `localStorage` (`admin_auth_token`, `admin_user`); nenhum endpoint revoga a sessão. Evidência em produção: sessão 119 do funcionário id 4 seguiu com `revogado_em` nulo depois do "Sair"; as 22 sessões desse funcionário nunca tinham sido revogadas. Um token copiado (o que ocorreu nesta data) vale até `expira_em` (12 h). O dossiê registra o mesmo para o portal do cliente (`auth_token`). Não há endpoint de logout no n8n (P1-8 não implementado).

**Objetivo.** Ao clicar em "Sair", a sessão correspondente ao token fica com `revogado_em` preenchido, de forma auditada, idempotente e sem revelar se o token existia; o frontend limpa o estado local mesmo se a chamada falhar.

**Escopo.**
- Dentro:
  1. `docs/integration/system_a_session_logout/004_up.sql` / `004_down.sql`: procedures `sp_funcionario_logout(p_token)` e `sp_cliente_logout(p_token)`, `SQL SECURITY INVOKER`, mesma validação de formato de token da T-0003 (`^[0-9A-Za-z]{20,128}$`), `UPDATE ... SET revogado_em = UTC_TIMESTAMP() WHERE token_hash = SHA2(p_token, 256) AND revogado_em IS NULL`, evento mínimo em `logs_auditoria` na mesma transação quando houve revogação (sem token nem hash no detalhe).
  2. Dois workflows n8n finos: `POST /admin/logout` e `POST /cliente/logout` (nomes finais a confirmar contra os caminhos existentes), token só do cabeçalho `Authorization: Bearer`, consulta parametrizada, resposta sempre `200 {"success": true}`, CORS restrito a `https://serdial21.com`, sem salvar dados de execução.
  3. Extensão do validador MariaDB do CI (procedures executadas de verdade): revoga só a sessão do token; token inválido/inexistente/já revogado não altera nada e devolve o mesmo resultado; repetição é idempotente; sessão de outro usuário intacta; auditoria gravada só quando revogou; rollback `004_down.sql`.
  4. Testes estáticos dos JSONs (Bearer, parâmetros, CORS, sem retenção, resposta neutra).
  5. Prompt para o Lovable: "Sair" (admin e cliente) chama o endpoint com o token atual e, em `finally`, limpa `localStorage` e redireciona — nunca bloqueia o logout local por falha de rede.
  6. Runbook de publicação e verificação.
- Fora (registrar na fila):
  - SG-10: workflows que validam sessão sem `revogado_em IS NULL` (ao menos `admin/permissoes/cliente`). Neles a revogação não vale. A T-0005 entrega a revogação; o inventário e a correção desses workflows exigem a exportação deles pelo usuário.
  - "Sair de todos os dispositivos" e revogação administrativa de sessões de terceiros.
  - Expiração por inatividade; troca de `NOW()` por `UTC_TIMESTAMP()` nos workflows de validação.

**Referências.**
- Internas: ADR 0018 e T-0003 (padrão de procedure `INVOKER`, formato de token, auditoria em `logs_auditoria`); `docs/integration/SYSTEM_A_SECURITY_GAPS.md` SG-10; dossiê itens 13 e P1-8; `docs/integration/SYSTEM_A_RUNTIME_VERIFICATION.md` ("LOGOUT REVOCATION: GAP").
- Externa aplicável: OWASP Session Management Cheat Sheet, seção "Session Expiration / Manual Session Expiration" — logout deve invalidar a sessão no servidor, não só no cliente. Versão consultada: a ser citada com data de acesso na implementação.

**Decisões propostas (precisam de aprovação).**
- **D1.** Revogação por procedure com migration `004` (testável no CI e auditada), não por `UPDATE` solto no n8n.
- **D2.** Resposta sempre `200 {"success": true}`, com ou sem sessão válida, para o endpoint não servir de verificador de tokens.
- **D3.** Revoga apenas a sessão do token apresentado (este dispositivo).
- **D4.** Auditoria: `acao = 'employee_logout'` (com `funcionario_id`) e `'client_logout'` (`funcionario_id` nulo, `tabela_afetada = 'security_sessoes_clientes'`, `registro_id = cliente_id`); só quando houve revogação.

**Critérios de aceite.**
1. Depois do "Sair", a sessão do token tem `revogado_em` preenchido (UTC) e o token é recusado pelos endpoints que verificam `revogado_em` (ex.: listagem de clientes da T-0003).
2. Sessões de outros usuários e outras sessões do mesmo usuário ficam intactas.
3. Token ausente, malformado, inexistente, expirado ou já revogado: nenhuma alteração, nenhuma auditoria, mesma resposta.
4. Repetir o logout é idempotente.
5. Revogação e auditoria na mesma transação.
6. Frontend limpa o estado local mesmo com falha de rede.
7. `004_down.sql` remove só os objetos da `004`.

**Riscos.**
- Revogação não vale nos workflows que não checam `revogado_em` (SG-10) — comunicado e registrado.
- Caminho do webhook do cliente: o portal pode chamar o n8n via `proxy-webhook` do Supabase (login do cliente usa esse caminho); o prompt do Lovable deve seguir o mesmo mecanismo das demais chamadas autenticadas do cliente.
- Mudança no Lovable depende de revisão do diff pelo usuário antes de publicar.
- Formato do token do cliente não confirmado. O do funcionário observado em produção tem 50 caracteres alfanuméricos; se o do cliente tiver outros caracteres, a validação `^[0-9A-Za-z]{20,128}$` transformaria o logout em no-op silencioso. Verificação antes de implementar: no navegador, após login de cliente, conferir comprimento e caracteres de `localStorage.auth_token` (sem copiar o valor).

**Ações do usuário (depois da implementação e do CI verde).** Backup; `004_up.sql` no phpMyAdmin; `verify` da 004; importar e ativar os dois workflows; aplicar o prompt no Lovable e revisar o diff; teste guiado (sair → `revogado_em` preenchido → token recusado).

---

## 2. Decisões do usuário

### [2026-10-03] Usuário
- Escopo: funcionários e clientes.
- Condução: Claude implementa (como na T-0004), sem Codex; exceção ao fluxo do protocolo decidida pelo usuário.
- Briefing (D1–D4): pendente.
- Verificação do token do cliente (usuário, console do navegador após login de cliente): comprimento 50; `/^[0-9A-Za-z]+$/` → `true`. Compatível com a validação `^[0-9A-Za-z]{20,128}$`. Risco encerrado.

### [2026-10-03] Usuário
- "aprovo" — D1 a D4 aprovadas como propostas.

---

## 3. Implementação (Claude)

### [2026-10-03] Claude — Implementação

- Arquivos criados (`docs/integration/system_a_session_logout/`): `004_up.sql`, `004_down.sql`, `verify_004.sql`, `n8n_admin_logout_v1.json` (`POST admin/logout-v1`), `n8n_client_logout_v1.json` (`POST cliente/logout-v1`), `LOVABLE_PROMPT.md`; `docs/integration/SYSTEM_A_SESSION_LOGOUT_RUNBOOK.md`; `tests/unit/test_system_a_session_logout_assets.py`.
- Arquivo alterado: `scripts/validate_system_a_client_management.sh` (aplica `004_up.sql` depois dos testes da 003, executa os cenários de logout e `004_down.sql`; novas linhas `SESSION_LOGOUT_TESTS=PASS` e `SESSION_LOGOUT_ROLLBACK=PASS`).
- Procedures: validam o formato do token; calculam o hash numa variável com a colação da coluna comparada (`utf8mb4_unicode_ci` para funcionários, `utf8mb4_uca1400_ai_ci` para clientes, conforme conferido em produção nesta data), para evitar o erro 1267; travam e revogam só a sessão viva do token (`revogado_em IS NULL` e `expira_em > UTC_TIMESTAMP()`); gravam auditoria só quando revogam, na mesma transação, com `JSON_OBJECT('request_id', ...)` apenas; devolvem sempre `success = 1, result = 'logged_out'`.
- Decisão técnica não prevista no briefing: sessão **expirada** não é marcada como revogada (critério 3 do briefing); ela já não autentica.
- Workflows: token só do `Authorization: Bearer`, consulta parametrizada, `200 {"success": true}` quando a procedure executou e `500 {"success": false}` em falha interna (não depende do token, portanto não revela validade), CORS restrito a `https://serdial21.com`, sem retenção de execução, sem credenciais no JSON.
- Testes: 7 estáticos passam; suíte local `524 passed, 20 skipped` (6 arquivos não coletados por falta de `redis` local, pré-existente); varredura de segredos `PASS`. **Não executado localmente:** o validador MariaDB (sem Docker na máquina). A primeira execução real das procedures será no CI após o push.
- Migrations: `004` do Sistema A (fora do Alembic, como 001–003).

**Pendências:** push pelo usuário; CI verde com `SESSION_LOGOUT_TESTS=PASS`; publicação conforme o runbook; inventário SG-10 (fila).

### [2026-10-03] Claude — CI verde (commit `3ba048d`, run 37156807733)

Conferido no log: `526 passed`; `CLIENT_MANAGEMENT_*` todos `PASS` (003 continua íntegra); `SESSION_LOGOUT_TESTS=PASS` e `SESSION_LOGOUT_ROLLBACK=PASS` — primeira execução real de `004_up.sql`/`004_down.sql` no MariaDB 11.8.9, incluindo a colação `utf8mb4_uca1400_ai_ci` da tabela de sessões de clientes; `pip-audit` sem vulnerabilidades; varredura de segredos `PASS`.

**Próximo passo:** publicação guiada pelo `docs/integration/SYSTEM_A_SESSION_LOGOUT_RUNBOOK.md`.
