# Runbook — "Sair" revoga a sessão no servidor (T-0005)

Artefatos: `docs/integration/system_a_session_logout/`
(`004_up.sql`, `004_down.sql`, `verify_004.sql`, `n8n_admin_logout_v1.json`,
`n8n_client_logout_v1.json`, `LOVABLE_PROMPT.md`).

Pré-requisito: CI verde com `SESSION_LOGOUT_TESTS=PASS` e
`SESSION_LOGOUT_ROLLBACK=PASS`.

## Ordem

1. **Pré-checagem (somente leitura).** Execute `verify_004.sql` no phpMyAdmin.
   A coluna `conferencia` das duas linhas de `token_hash` deve ser `OK`. Se
   aparecer `DIVERGENTE - NAO APLICAR`, pare: as procedures comparam o hash com
   a colação da coluna e falhariam com erro 1267.
2. **Backup** do banco pelo phpMyAdmin (Exportar → Personalizado, incluindo
   `CREATE PROCEDURE`), guardado fora do repositório.
3. **Migration.** Importe `004_up.sql` pela aba Importar. Esperado: sucesso,
   com avisos `#1305 does not exist` nos `DROP ... IF EXISTS`.
4. **Conferência.** Execute `verify_004.sql` de novo: a última consulta lista
   `sp_cliente_logout` e `sp_funcionario_logout`, ambas `INVOKER`.
5. **n8n.** Importe os dois JSONs (entram inativos e sem credenciais). Em cada
   um, associe a credencial MySQL do `u621451815_serdial21user` ao nó
   "Revogar Sessao", salve e ative. Os paths `admin/logout-v1` e
   `cliente/logout-v1` são novos; se a ativação acusar conflito, pare e
   verifique qual workflow já usa o path.
6. **Teste do endpoint antes do frontend.** Logado como funcionário de teste,
   no console do navegador (sem copiar o token):
   `fetch('https://n8n.serdial21.com/webhook/admin/logout-v1', {method: 'POST', headers: {Authorization: 'Bearer ' + localStorage.admin_auth_token}}).then(r => r.status)`.
   Esperado: `200`. No phpMyAdmin, a sessão mais recente do funcionário tem
   `revogado_em` preenchido e há um evento `employee_logout` em
   `logs_auditoria`. Telas que verificam `revogado_em` passam a exigir login.
7. **Lovable.** Aplique `LOVABLE_PROMPT.md`, revise o diff (só as funções de
   logout) e publique.
8. **Teste final.** Funcionário: entrar, "Sair", conferir `revogado_em`.
   Cliente: entrar no portal, "Sair", conferir `revogado_em` da sessão mais
   recente do cliente e o evento `client_logout`.

## Rollback

- Frontend: reverter a publicação no Lovable (o logout volta a ser só local).
- n8n: desativar os dois workflows.
- Banco: importar `004_down.sql`. Sessões já revogadas e eventos de auditoria
  permanecem como histórico.

## Limitação conhecida

Workflows que validam sessão sem `revogado_em IS NULL` continuam aceitando o
token revogado até `expira_em` (SG-10; ao menos `admin/permissoes/cliente`).
Inventário e correção ficam na fila do QUADRO.
