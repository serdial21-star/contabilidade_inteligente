# T-0004 — Menu do Operador vazio: leitura de permissões do funcionário falha no n8n

| Campo | Valor |
|---|---|
| Estado | CONCLUÍDA — aplicada em 03/10/2026 |
| Origem | QUADRO, fila item 15; teste da T-0003 em 03/10/2026 |
| Sistema | Sistema A (artefato versionado em `docs/integration/system_a_permissions/`) |
| Exige ADR | não |
| Exige ação do usuário | sim — ajustar três nós no workflow ativo do n8n e testar |

---

## 1. Diagnóstico e briefing (Claude)

### [2026-10-03] Claude — Diagnóstico

**Sintoma.** Logado como Operador (funcionário id 4), o painel administrativo mostra a barra lateral sem itens. `POST https://n8n.serdial21.com/webhook/admin/permissoes/funcionario` responde 200 com corpo vazio; o console mostra `[usePermissoes] Resposta inválida do servidor: null`. As execuções do workflow "API - Admin - Permissões (Funcionários) v2.2 (Token + Fallback) (Com Sessão, leitura corrigida)" terminam em erro (ex.: 36655, 36657, 36661, 36666).

**Erro registrado (execução 36666, n8n 2.6.4):** `ExpressionError: "Validar Sessão" node has 1 item(s) but you're trying to access item 1`, num nó MySQL `executeQuery`.

**Causas (lidas no JSON ativo, versionado sem alteração no commit `080322b`):**
1. "Buscar Módulos" devolve uma linha por permissão (40 para o funcionário id 4). "Buscar Clientes Acesso" roda uma vez por item de entrada e usa `$node['Validar Sessão'].json.id`; a partir do segundo item o n8n procura o item correspondente em "Validar Sessão", que tem um só → erro.
2. O código de "Montar Permissões" não compila: falta a `}` que fecha `fallbackPorCargo` depois do retorno do caso Operador (42 `{` para 41 `}`). Provável efeito colateral da edição que restringiu o fallback do Operador a "só visualizar" (SG-19).
3. Latente: funcionário sem nenhuma linha em `permissoes_funcionario_modulos` faz "Buscar Módulos" não emitir item; o fluxo para sem responder (corpo vazio). É o "retorno vazio causa tela branca" de `docs/integration-input/DOSSIE_SERDIAL21.md`.

Os Administradores também têm 40 linhas e provavelmente também recebem corpo vazio; o menu deles aparece porque o frontend libera por cargo.

**Ponto de segurança a preservar.** Em 21/09 o frontend liberava tudo com lista vazia (`docs/integration-input/RELATORIO_VARREDURA_LOVABLE_20260921.md`). Hoje o menu some com resposta inválida, o que é fail-closed. A correção é no workflow; o frontend não deve voltar a liberar com resposta vazia.

### [2026-10-03] Claude — Escopo

- Dentro: as três causas acima, no caminho de leitura.
- Fora (fila, item 18): CORS `*`; `NOW()` em vez de `UTC_TIMESTAMP()` na validação de sessão; SQL por interpolação; gravação com DELETE+INSERT sem transação nem auditoria; a leitura ignora o `funcionario_id` do corpo e devolve as permissões da sessão (verificar se a tela de Permissões do Administrador depende dele); fallback por cargo quando não há linhas (SG-19, decisão de produto pendente).

---

## 2. Decisões do usuário

### [2026-10-03] Usuário
- Condução: "Claude corrige agora" — Claude versiona o workflow, aplica só as três correções, escreve testes e registra; sem implementação pelo Codex nem revisão cruzada. Exceção ao fluxo do protocolo decidida pelo usuário.
- Demais problemas: "Fila, tarefa separada".

---

## 3. Implementação (Claude)

### [2026-10-03] Claude — Implementação

- Arquivos criados: `docs/integration/system_a_permissions/n8n_admin_permissoes_funcionario_v2_2.json` (commit `080322b`, cópia fiel do workflow ativo); `tests/unit/test_system_a_permissions_workflow.py`.
- Alterações no workflow (diff sobre `080322b`):
  1. "Buscar Clientes Acesso": `executeOnce: true`; consulta passa a usar `$('Validar Sessão').first().json.id`; `alwaysOutputData: true`.
  2. "Buscar Módulos": `alwaysOutputData: true`. "Montar Permissões" já ignora itens sem `modulo`/`acao` e sem `cliente_id`.
  3. "Montar Permissões": inserida a `}` que fecha `fallbackPorCargo`.
- Nada mais mudou (credenciais, webhooks, caminho de gravação, CORS e consultas de sessão intocados).
- Testes: 3 novos, estáticos (não há Node no ambiente para executar o JS); passam com a correção e falham os 3 no JSON de `080322b`. Suíte local: `517 passed, 20 skipped`; 6 arquivos não coletados por falta de `redis` no ambiente local (pré-existente). Varredura de segredos: `PASS`.
- Limitação: os testes não executam o workflow; a validação real é o teste no n8n descrito abaixo.

**Aplicação (usuário, no workflow ativo, sem reimportar):**
1. "Buscar Clientes Acesso" → Settings: ligar **Execute Once** e **Always Output Data**; em Query, trocar `$node['Validar Sessão'].json.id` por `$('Validar Sessão').first().json.id`.
2. "Buscar Módulos" → Settings: ligar **Always Output Data**.
3. "Montar Permissões": logo depois do bloco `listas: { visualizar: true }` + `};` do caso Operador, acrescentar uma linha só com `}` antes de `if (!hasModulos) {`.
4. Salvar.

**Teste:** entrar como Operador → menu aparece com os módulos liberados; execução do workflow em "Success"; resposta de `.../permissoes/funcionario` com `success: true` e `modulos`. Repetir como Administrador. Ao terminar, revogar a sessão de teste do Operador (o logout não revoga; fila item 17).

### [2026-10-03] Claude — Aplicação confirmada e encerramento

- O usuário informou que os três ajustes já tinham sido aplicados no workflow ativo e que o menu está funcionando. Não foi transcrito o status das execuções no n8n nem conferido, nó a nó, que o workflow ativo é idêntico ao commit `1672aae`; a evidência é funcional (menu do Operador exibido).
- Pendências fora do escopo: fila, item 18 (endurecimento do workflow de permissões).

**Estado: CONCLUÍDA.**
