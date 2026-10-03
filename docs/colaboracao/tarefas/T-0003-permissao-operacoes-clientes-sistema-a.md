# T-0003 — Exigir permissão nas operações administrativas de clientes do Sistema A

| Campo | Valor |
|---|---|
| Estado | CI VERDE — aguardando publicação guiada (phpMyAdmin e n8n) |
| Origem | Item 1 do QUADRO; auditoria de segurança de 01/10/2026, achado #3 (ALTA) |
| Sistema | Sistema A (artefatos versionados em `docs/integration/system_a_client_management/`) |
| Exige ADR | sim — `docs/adr/0018-autorizacao-por-permissao-clientes-sistema-a.md` (Proposta) |
| Exige ação do usuário | sim — diagnóstico antes da aprovação; publicação no phpMyAdmin e no n8n depois do aceite |

---

## 1. Briefing (Claude)

### [2026-10-01] Claude — Briefing

**Problema.** Qualquer funcionário ativo, de qualquer cargo, consegue listar, criar e editar clientes chamando os webhooks diretamente com o próprio token. A autenticação existe; a autorização não:

- listagem: `n8n_admin_client_list_v2.json`, nó "Validar Sessao Admin" — só sessão válida e `f.status = 'Ativo'`;
- criação: `001_up.sql:149-171` (`sp_admin_cliente_create`) — idem;
- edição: `002_up.sql:98-120` (`sp_admin_cliente_update`) — idem.

Cenário concreto: um funcionário `Auditor` chama `editar-cliente-v2` e troca o e-mail de um cliente. Depois pede `portal/solicitar-senha` para o novo e-mail e assume o Portal do Cliente. Agravantes no mesmo fluxo:

- a troca de e-mail não revoga as sessões do cliente nem os links pendentes (`002_up.sql:202-213` só revoga quando o status deixa de ser `Ativo`);
- a auditoria grava só status anterior e novo (`002_up.sql:235-246`), sem rastro da troca de e-mail ou documento.

**Objetivo.** As três operações passam a exigir permissão verificada no banco, conforme o ADR 0018, e a troca de e-mail fica rastreada e segura.

**Escopo.**
- Dentro:
  1. Nova migração `003_up.sql` / `003_down.sql` em `docs/integration/system_a_client_management/`, com uma rotina única de autenticação + autorização por `(modulo, acao)` e a substituição de `sp_admin_cliente_create` e `sp_admin_cliente_update`. Se a listagem for mais segura como procedure (ex.: `sp_admin_cliente_list`), criá-la e ajustar o workflow para chamá-la.
  2. Regra de autorização conforme **D1** (seção 2, quando decidida).
  3. Troca de e-mail e de documento conforme **D2** (seção 2, quando decidida).
  4. Na troca de e-mail: revogar sessões do cliente e links pendentes na mesma transação.
  5. Auditoria: `email_changed` e `document_changed` com SHA-256 do valor anterior e do novo; registrar negações por permissão (`client_action_forbidden`, com módulo e ação, sem dados do cliente).
  6. Resultado `forbidden` distinto de `unauthorized`; os três workflows mapeiam `unauthorized` → 401 e `forbidden` → 403, mantendo os contratos de sucesso e de erro existentes.
  7. Atualizar os 3 JSONs de workflow, o `test_base_schema.sql` (tabela de permissões com a estrutura real informada pelo usuário e funcionários sintéticos de cada cargo), `verify.sql`, `scripts/validate_system_a_client_management.sh`, `tests/unit/test_system_a_client_management_assets.py` e o runbook.
  8. Executar `scripts/validate_system_a_client_management.sh` no CI do GitHub (job com Docker no runner Ubuntu), porque o computador do usuário não roda Docker e esta é a única forma de executar as procedures de verdade antes da publicação.
- Fora:
  - restrição por cliente (`permissoes_funcionario_clientes`) e exclusão de clientes;
  - ajustes de tela no Lovable (esconder botões conforme a matriz) — tarefa separada;
  - conceder permissões automaticamente (nada de backfill: o administrador concede pela tela de Permissões);
  - login legado de clientes e o workflow "[SECURITY] Validar Sessão de Funcionário" (itens 7 e 2 da fila).

**Referências.**
- Consultadas e aplicáveis:
  - `docs/integration/SYSTEM_A_SECURITY_GAPS.md` — SG-03 (fail-open, corrigido em 22/09 com negação por padrão), SG-19 (fallback por cargo), SG-11 (cobertura de auditoria);
  - `docs/integration/SYSTEM_A_RUNTIME_VERIFICATION.md:206` — `permissoes_funcionario_modulos` existe em produção;
  - `PROMPT_PERMISSOES_N8N_MYSQL.md` (cópia local do código do Sistema A, fora deste repositório) — matriz `modulo`/`acao`/`permitido`, middleware fail-closed e mapeamento listar/criar/editar;
  - `docs/integration/SYSTEM_A_CLIENT_MANAGEMENT_RUNBOOK.md` — contratos preservados e rollback;
  - OWASP ASVS 4.0.3, capítulo V4 (Access Control): controle de acesso aplicado em camada confiável no servidor (V4.1.1), atributos de autorização não manipuláveis pelo cliente (V4.1.2 — o cargo vem do banco, não do navegador), menor privilégio (V4.1.3), falha segura (V4.1.5) e registro das decisões de acesso negadas (V7.2.2). Conferir a redação na versão oficial antes de citar em código. Usado como critério técnico; o projeto ainda não adotou formalmente um nível do ASVS (ver `docs/colaboracao/REFERENCIAS.md`).
  - LGPD (Lei 13.709/2018), art. 46: medidas de segurança aptas a proteger dados pessoais de acessos não autorizados. O e-mail e o documento do cliente são dados pessoais quando o cliente é pessoa física.
- Procuradas e não encontradas: nenhuma política escrita do escritório define quem pode trocar e-mail ou documento de cliente. Por isso o D2 é decisão do usuário.
- Ressalva: a cópia local do código do Sistema A está desatualizada (não contém a tela de edição publicada em 30/09). Ela foi usada só para o modelo de permissões, não como retrato do que está no ar.

**Restrições.**
- `AGENTS.md` 6.7: o efeito e o evento de auditoria na mesma transação; 6.9: nada de e-mail ou documento em claro na auditoria nem em log.
- Contratos preservados do runbook: caminhos, métodos, `multipart/form-data` na edição, `funcionario_id` do formulário ignorado.
- Workflows continuam com `saveDataSuccessExecution`/`saveDataErrorExecution` restritos e consultas com parâmetros (testes existentes cobrem isso).
- A migração `003` precisa de `003_down.sql` que restaure exatamente as procedures de `002`, sem apagar dados nem auditoria.
- Nada é executado contra o banco ou o n8n reais pelo Codex ou pelo Claude.

**Critérios de aceite.**
1. Sessão inválida, expirada ou revogada → `unauthorized`, nenhum efeito.
2. Sessão válida sem permissão para a ação → `forbidden`, nenhum efeito no cliente, evento de negação auditado.
3. `Administrador` e `Admin` (cargo lido do banco) → autorizados nas três operações.
4. `Operador` com `('clientes','criar', permitido = 1)` cria; sem a linha, ou com `permitido = 0`, recebe `forbidden`. O mesmo para `visualizar` e `editar`.
5. `Auditor` sem `editar` → `forbidden` na edição; com `visualizar` → lista.
6. Cargo vazio, nulo ou desconhecido sem linha → `forbidden`.
7. Troca de e-mail ou documento por quem não atende ao D2 → `forbidden`, nada alterado.
8. Troca de e-mail autorizada → sessões do cliente e links pendentes revogados, evento `email_changed` com os dois hashes, tudo na mesma transação.
9. Troca de documento autorizada → evento `document_changed` com os dois hashes.
10. Edição sem troca de e-mail ou documento por quem tem `editar` → funciona como hoje.
11. `003_down.sql` restaura o comportamento de `002`.
12. Suíte padrão sem falhas; `validate_system_a_client_management.sh` passa no CI.

**Testes exigidos** (no script de validação, contra MariaDB 11.8.9 descartável, e nos testes de ativos):
1. Um caso por critério de 1 a 11, com funcionários sintéticos `Administrador`, `Admin`, `Operador` (com e sem linhas), `Auditor` e cargo desconhecido.
2. Verificação de que nenhum evento de auditoria contém e-mail ou documento em claro.
3. Teste de ativos garantindo que os workflows mapeiam `forbidden` para 403 e `unauthorized` para 401.

**Riscos e pontos de atenção.**
- **Bloqueio no dia da publicação:** quem não tiver as linhas de permissão deixa de trabalhar com clientes. Mitigação: o diagnóstico abaixo e a concessão pela tela antes da publicação.
- A grafia dos cargos é texto livre (`VARCHAR(50)`). Comparar sem diferenciar maiúsculas e sem espaços nas pontas, mas não aceitar variações além de `Administrador` e `Admin`.
- A estrutura real da tabela de permissões pode divergir do prompt do Sistema A; o teste sintético deve reproduzir a estrutura real.
- A edição também envia a logo ao Google Drive depois do commit; a autorização precisa acontecer antes de qualquer efeito, inclusive no Drive.

**Ações do usuário.**

*Agora, antes de aprovar (somente leitura, no phpMyAdmin do banco do Sistema A, aba SQL):*

1. Estrutura da tabela (não mostra dados):
   ```sql
   SHOW CREATE TABLE permissoes_funcionario_modulos;
   ```
2. Situação das permissões de clientes por funcionário ativo (sem nomes nem e-mails):
   ```sql
   SELECT f.id, f.cargo,
          SUM(p.modulo = 'clientes' AND p.acao = 'visualizar' AND p.permitido = 1) AS ver,
          SUM(p.modulo = 'clientes' AND p.acao = 'criar'      AND p.permitido = 1) AS criar,
          SUM(p.modulo = 'clientes' AND p.acao = 'editar'     AND p.permitido = 1) AS editar,
          COUNT(p.id) AS linhas_total
     FROM funcionarios AS f
     LEFT JOIN permissoes_funcionario_modulos AS p ON p.funcionario_id = f.id
    WHERE f.status = 'Ativo'
    GROUP BY f.id, f.cargo
    ORDER BY f.id;
   ```
3. Copiar os dois resultados para o Claude.

*Depois do aceite:* publicação com backup, `003_up.sql` no phpMyAdmin e importação dos 3 workflows no n8n — o passo a passo será escrito no runbook e no encerramento.

---

## 2. Decisões do usuário

*Decididas:*

### [2026-10-01] Usuário
- **D1:** conforme recomendado — `Administrador`/`Admin` (cargo lido do banco) sempre autorizado; demais cargos somente com `permitido = 1` na matriz para `('clientes', ação)`; sem linha, `permitido = 0`, cargo vazio ou desconhecido → negado.
- **D2:** conforme recomendado — troca de e-mail ou de CPF/CNPJ de cliente exige cargo `Administrador`/`Admin`, mesmo para quem tem `clientes.editar`.

*Diagnóstico recebido (abaixo). Falta apenas a aprovação do briefing pelo usuário.*

### [2026-10-01] Usuário — Diagnóstico (transcrito pelo Claude a partir de captura de tela do phpMyAdmin)
- 7 funcionários ativos: ids 1 e 3 com cargo `Administrador`; ids 2, 4, 5, 6 e 7 com cargo `Operador`. Nenhum `Auditor`, `Admin` ou cargo desconhecido.
- Todos os 7 têm `clientes.visualizar`, `clientes.criar` e `clientes.editar` com `permitido = 1`, e 40 linhas de permissão no total cada um.
- Consequência: a regra D1 não bloqueia ninguém na publicação. O efeito prático imediato é o D2: os 5 Operadores deixam de poder trocar e-mail ou CPF/CNPJ de cliente.
- Observação para decisão futura (fora desta tarefa): 40 linhas por funcionário indicam todas as combinações de módulo e ação cadastradas; convém o usuário revisar na tela de Permissões se os Operadores devem ter todas liberadas.
- Pendente: estrutura da tabela. O `SHOW CREATE TABLE` saiu truncado na tela; foi pedida a consulta equivalente em `information_schema.COLUMNS` e `SHOW INDEX`.

### [2026-10-01] Usuário — Estrutura de `permissoes_funcionario_modulos` (transcrita pelo Claude da aba Estrutura do phpMyAdmin)
- Colunas: `id INT(11) NOT NULL AUTO_INCREMENT`; `funcionario_id INT(11) NOT NULL`; `modulo VARCHAR(50) NOT NULL`; `acao VARCHAR(20) NOT NULL`; `permitido TINYINT(1) NOT NULL DEFAULT 1`; `criado_em DATETIME NULL DEFAULT current_timestamp()`; `atualizado_em DATETIME NULL DEFAULT current_timestamp() ON UPDATE current_timestamp()`. Colação `utf8mb4_unicode_ci`.
- Índices: `PRIMARY (id)`; `UNIQUE uk_func_modulo_acao (funcionario_id, modulo, acao)`; `idx_func_id (funcionario_id)`.
- Chave estrangeira para `funcionarios`: não confirmada na captura (a aba "Visão de relação" não foi aberta). O teste sintético pode declará-la; ela não altera a regra de autorização.
- 280 linhas (7 funcionários × 40).

**Diagnóstico completo.** O `test_base_schema.sql` deve reproduzir exatamente as colunas e índices acima.

### [2026-10-01] Usuário — Aprovação
- Aprovou o briefing ("aprovado T-0003"). Com isso, o ADR 0018 passa a **Aceita**, com D1 e D2 conforme recomendado.

### [2026-10-01] Usuário — D3 e D4
- **D3:** conforme recomendado — Operador com `clientes.editar` pode preencher o **primeiro** CPF/CNPJ de um Lead (documento anterior vazio); trocar documento já existente continua exigindo `Administrador`/`Admin`. E-mail continua sempre exigindo `Administrador`/`Admin`, inclusive quando o cliente não tinha e-mail.
- **D4:** conforme recomendado — a auditoria registra apenas que a alteração ocorreu (`email_changed`, `document_changed`, com funcionário, data e `request_id`), **sem hash** nem valor de e-mail ou documento. Altera o item 5 do ADR 0018 (registrado como emenda no próprio ADR).

---

## 3. Implementação (Codex)

### [2026-10-01] Codex — Implementação

**Resultado.**

A autorização das três operações administrativas foi centralizada no banco e
implementada conforme D1 e D2. A listagem deixou de autenticar por SQL inline e
passou a chamar procedure. Criação e edição revalidam sessão, cargo e permissão
na transação antes do efeito. `unauthorized` e `forbidden` permanecem distintos
até a resposta HTTP (401/403).

**Arquivos criados.**

- `docs/integration/system_a_client_management/003_up.sql`;
- `docs/integration/system_a_client_management/003_down.sql`.

**Arquivos alterados.**

- `.github/workflows/ci.yml`;
- `docs/integration/SYSTEM_A_CLIENT_MANAGEMENT_RUNBOOK.md`;
- os três workflows administrativos de listagem, criação e edição;
- `docs/integration/system_a_client_management/test_base_schema.sql`;
- `docs/integration/system_a_client_management/verify.sql`;
- `scripts/validate_system_a_client_management.sh`;
- `tests/unit/test_system_a_client_management_assets.py`;
- `docs/colaboracao/QUADRO.md` e este arquivo de tarefa.

**Implementação técnica.**

- `sp_admin_client_authorize` resolve sessão e cargo no banco, concede acesso
  integral somente a `Administrador`/`Admin` e exige `permitido = 1` dos demais.
  Ausência de linha, negação explícita, cargo vazio/nulo ou desconhecido falham
  fechados. Negação por permissão gera `client_action_forbidden`, sem id ou dado
  do cliente.
- `sp_admin_cliente_list` aplica `clientes.visualizar` e retorna uma linha de
  metadados mais as linhas dos clientes. Essa forma preserva o array público e
  evita agregar toda a listagem em um JSON sujeito a limite de tamanho.
- `sp_admin_cliente_create` exige `clientes.criar`; o workflow só alcança Google
  Drive depois do sucesso autorizado no banco.
- `sp_admin_cliente_update` exige `clientes.editar`. Troca de e-mail ou documento
  exige adicionalmente cargo administrativo. A troca de e-mail revoga sessões e
  links pendentes na mesma transação. Os eventos `email_changed` e
  `document_changed` guardam somente hashes anterior/novo.
- `003_down.sql` remove a fronteira nova e a procedure de listagem e recria as
  procedures de criação/edição com o comportamento vigente após `002_up.sql`,
  sem remover dados ou auditoria.
- A fixture reproduz as colunas e índices diagnosticados da tabela de permissões
  e inclui cargos/permissões sintéticos positivos e negativos.
- O validador descartável cobre sessões inválida, expirada e revogada; cargos
  administrativos; permissão concedida, ausente e negada; auditor, cargo
  desconhecido e nulo; D2; revogação; hashes; ausência de dados em claro; e
  downgrade.

**Validação executada.**

- Testes específicos dos ativos: `20 passed`.
- Suíte unitária: `286 passed`.
- Suíte completa: `609 passed, 20 skipped`, com os 2 avisos de depreciação já
  existentes. Os 20 ignorados dependem de opt-in/ambiente MariaDB.
- Varredura de segredos: canário e release `PASS`.
- Os três JSONs foram parseados com sucesso.
- `bash -n scripts/validate_system_a_client_management.sh`: `PASS` no Git Bash.
- `git diff --check`: sem erro; apenas avisos de normalização LF/CRLF.

**Validação pendente e risco residual.**

O ciclo funcional de `001` → `002` → `003` → downgrade não foi executado nesta
máquina, conforme o briefing: ele requer MariaDB 11.8.9 descartável e deve rodar
no novo passo do CI Ubuntu. Portanto, sintaxe e semântica reais das procedures
003 ainda precisam do primeiro CI verde antes da publicação. Nenhum banco, n8n,
Google Drive ou API real foi acessado.

**Migrations e decisões.**

- Migration do Sistema A criada: `003_up.sql` / `003_down.sql`. Nenhuma migration
  Alembic foi criada.
- Não houve backfill nem concessão automática de permissão.
- A publicação continua ação exclusiva do usuário, após revisão, CI verde,
  backup e confirmação da matriz, seguindo o runbook atualizado.

---

## 4. Revisões (Claude) e respostas (Codex)


### [2026-10-01] Claude — Revisão 1

**Veredito: AJUSTES.** A autorização está correta no essencial: nenhum caminho de bypass encontrado, autorização antes de qualquer efeito (Drive, logo e e-mail só no ramo de sucesso), `unauthorized` com ROLLBACK, `forbidden` com COMMIT apenas do evento de negação, `permitido` nulo/ausente e cargo nulo/vazio negados, `003_down.sql` idêntico a 001/002 (diferenças só de espaço), contrato da listagem preservado (`{ success, data }`). Mas há um defeito que afeta o uso real, uma perda de cobertura num fluxo em produção e duas decisões novas para o usuário.

**Verificado pelo Claude:** leitura integral de `003_up.sql`; estrutura e conexões dos 3 workflows; contrato da resposta da listagem antes e depois; suíte padrão 609 aprovados, 20 ignorados, 0 falhas; varredura de segredos `PASS`; `bash -n` válido; `git diff --check` limpo. Auditoria independente pelo agente `cacador-de-bugs` (0 crítico, 0 alto, 2 médios, 3 baixos; nenhum bypass). Achados abaixo conferidos no código pelo Claude.

**Bloqueantes (Codex)**
1. **E-mail principal divergente (MÉDIA).** A listagem devolve `email` = `MIN(e.email)` (ordem alfabética, `003_up.sql:141`), mas a edição compara e grava o primeiro e-mail por `e.id` (`003_up.sql:439-445`, `463`, `536-540`). Num cliente com dois e-mails em que o primeiro por id não é o menor alfabético, um Operador que só muda o telefone recebe 403, e um Administrador recebe 409 ou sobrescreve o e-mail errado. Correção: a listagem devolve como `email` o primeiro por `e.id` (mesmo critério da edição). Teste: cliente com dois e-mails nessa condição; Operador reenvia o `email` da listagem mudando só o telefone → `updated`.
2. **Cobertura perdida (MÉDIA).** O validador deixou de testar o fluxo de redefinição do portal (`sp_cliente_password_reset_apply`: sucesso e reuso → `invalid_or_expired`), que está em produção desde 30/09 (conferido: 2 ocorrências em `HEAD`, 0 agora). Reincluir. Completar ainda:
   - critério 4: `visualizar` e `editar` negados (sem linha e com `permitido = 0`), não só `criar`;
   - critério 6: cargo vazio e cargo só com espaços;
   - critério 2: depois de cada `forbidden`, conferir com `assert_scalar` que nada foi inserido ou alterado e que a listagem negada não devolve linhas de cliente;
   - critério 3: `Admin` também em `criar`;
   - critério 1: `unauthorized` também em listagem e edição;
   - em `tests/unit/test_system_a_client_management_assets.py`, trocar o assert que procura palavras no arquivo inteiro por um que verifique o `SELECT` da procedure, e restaurar a verificação removida sobre `status = 'Ativo'`.
3. **Cargo comparado com colação que ignora acento (BAIXA).** `003_up.sql:58` e `467` comparam sem `COLLATE`; em `utf8mb4_unicode_ci`, `Admín` ou `ÁDMIN` passam como administrador, contra o briefing ("não aceitar variações além de `Administrador` e `Admin`"). Correção: comparação binária (`COLLATE utf8mb4_bin` ou `BINARY`) sobre o valor já em minúsculas e sem espaços. Teste: `Admín` sem linhas → `forbidden`; `' ADMIN '` → autorizado.
4. **401 nos workflows de criar e editar (BAIXA).** Sem `Authorization`, o nó "Validar e Normalizar" lança erro e o n8n responde com erro de execução, não 401. Enviar token vazio à procedure, como a listagem já faz.
5. **Hash da string vazia (BAIXA).** Ver D4 abaixo; se a decisão mantiver hash, usar `NULL` quando não havia valor anterior.
6. **Pré-publicação verificável.** Acrescentar ao `verify.sql` (somente leitura) as consultas de colação padrão do schema e das colunas comparadas, índices de `security_sessoes_funcionarios` e um lembrete de `SHOW GRANTS` do usuário do n8n. Motivo: `SQL SECURITY INVOKER` exige que o usuário do n8n leia `permissoes_funcionario_modulos`, e uma colação diferente em produção pode causar erro 1267; o CI roda como root com outra colação e não pegaria nenhum dos dois.
7. **Rollback dos workflows.** Gerar como artefato o JSON anterior da listagem (a partir de `git show HEAD:`), porque depois de `003_down.sql` a listagem nova deixa de funcionar.
8. **`sp_admin_cliente_set_folder`** (`001_up.sql:278-365`) continua só autenticada. Passar a usar `sp_admin_client_authorize` com `('clientes','criar')`.

**Decisões novas para o usuário (seção 2)** — o Codex aplica conforme a decisão:
- **D3 — Primeiro CPF/CNPJ de um Lead.** Pelo D2 atual, um Operador não consegue completar um Lead (documento vazio → preenchido), porque isso conta como troca. Recomendação do Claude: permitir ao Operador preencher o **primeiro** documento; trocar documento existente continua só Administrador. E-mail continua sempre só Administrador.
- **D4 — Hash na auditoria.** SHA-256 de CPF sem chave secreta é revertido por tentativa em segundos (há cerca de 1 bilhão de CPFs possíveis); o hash só aparenta proteger. Recomendação do Claude: registrar **apenas que houve troca** (quem, quando, `request_id`), sem hash do valor. Isso altera o item 5 do ADR 0018 e exige aprovação.

**Pontos para o teste após a publicação** (ação do usuário, entra no runbook): na listagem real, o número de clientes devolvido deve ser igual ao total da tabela (risco de o n8n incluir uma linha técnica do `CALL` como se fosse cliente).

**Sobre o CI:** o validador entrou no CI, mas só roda depois do push. A publicação no phpMyAdmin e no n8n só acontece depois de o CI ficar verde com o validador.

### [2026-10-01] Codex — Resposta parcial à Revisão 1

Os achados independentes de D3 e D4 foram atendidos. A tarefa permanece em
`AJUSTES` aguardando as duas decisões do usuário; nenhuma alteração de política
foi inferida.

**Correções aplicadas.**

1. A listagem agora usa o primeiro e-mail por `id`, igual à leitura e à gravação
   da edição. O validador cria um segundo e-mail alfabeticamente menor, confirma
   qual foi listado e prova que o Operador altera apenas o telefone sem 403.
2. O validador voltou a cobrir aplicação e reuso do reset do portal. Também
   passou a cobrir `visualizar` e `editar` sem linha e com negação explícita,
   cargo vazio, cargo com espaços, `Admin` criando, `unauthorized` em listagem e
   edição, ausência de efeito em cada negação e ausência de linhas de cliente na
   listagem negada. Ao final, confirma exatamente 15 eventos de negação sem
   `registro_id`.
3. Os cargos administrativos são comparados com semântica binária depois de
   `LOWER`/`TRIM`: cargo acentuado é negado e ` ADMIN ` é autorizado.
4. Criação e edição encaminham token vazio à procedure antes das validações do
   corpo, permitindo resposta 401 em vez de erro de execução do n8n.
5. Enquanto D4 não é decidida, os hashes aprovados foram mantidos; ausência de
   valor agora produz `NULL`, nunca o hash da string vazia.
6. `verify.sql` passou a expor collation do schema e colunas comparadas, índices
   das sessões administrativas e lembrete verificável de `SHOW GRANTS` para o
   usuário/host reais do n8n. O runbook inclui essa conferência.
7. Foi criado `n8n_admin_client_list_v2_rollback.json`, cópia do artefato de
   listagem anterior obtida de `HEAD`, e o runbook passou a referenciá-la.
8. `sp_admin_cliente_set_folder` agora revalida `clientes.criar` pela fronteira
   central. O downgrade recria a versão anterior dessa procedure.
9. O runbook exige comparar o tamanho do array real da listagem com o total da
   tabela depois da publicação, para detectar eventual linha técnica do `CALL`.

**Testes.**

- Testes específicos: `24 passed`.
- Suíte completa: `613 passed, 20 skipped`, com os mesmos 2 avisos preexistentes.
- Quatro JSONs parseados; sintaxe Bash válida; `git diff --check` sem erro.
- O ciclo MariaDB descartável permanece destinado ao CI Ubuntu, como definido
  no briefing.

**Decisões ainda necessárias.**

- D3: permitir ou não que Operador com `clientes.editar` preencha o primeiro
  CPF/CNPJ de Lead; a recomendação do Claude é permitir somente a primeira
  inclusão, mantendo troca posterior restrita a Administrador/Admin.
- D4: manter hashes de e-mail/documento ou registrar apenas a ocorrência; a
  recomendação do Claude é remover os hashes, porque SHA-256 sem chave não
  protege adequadamente um espaço pequeno como CPF.

Depois dessas decisões, o Codex precisa concluir SQL, testes, ADR e relatório e
então devolver a tarefa para nova revisão.

### [2026-10-01] Codex — Resposta final à Revisão 1

As decisões D3 e D4 foram aplicadas e os ajustes da Revisão 1 estão completos.
A tarefa retorna para revisão do Claude.

**D3 — primeiro documento do Lead.**

- Quem possui `clientes.editar` pode preencher o primeiro CPF/CNPJ somente
  quando o registro bloqueado para atualização ainda não possui documento e o
  status anterior é `Lead`.
- E-mail alterado continua exigindo `Administrador`/`Admin`, inclusive quando
  ainda não existia e-mail autorizado.
- Substituir ou remover documento existente continua exigindo cargo
  administrativo. O validador comprova a primeira inclusão, a substituição
  negada e a ausência de efeito; também comprova a negação do primeiro e-mail.

**D4 — auditoria mínima.**

- `email_changed` e `document_changed` mantêm funcionário, data, registro e
  `request_id`, mas não guardam valor anterior, valor novo nem hashes.
- O validador exige que `detalhes` contenha somente `request_id` e confirma a
  ausência das antigas chaves de hash e dos valores sintéticos.

**Arquivos ajustados nesta resposta.**

- `docs/integration/system_a_client_management/003_up.sql`;
- `scripts/validate_system_a_client_management.sh`;
- `tests/unit/test_system_a_client_management_assets.py`;
- `docs/integration/SYSTEM_A_CLIENT_MANAGEMENT_RUNBOOK.md`;
- este arquivo e `docs/colaboracao/QUADRO.md` para devolver o trabalho à
  revisão.

Os demais arquivos criados e alterados permanecem os listados no relatório de
implementação anterior. A migration continua sendo `003_up.sql` / `003_down.sql`;
nenhuma migration Alembic foi criada.

**Validação final.**

- Testes específicos dos ativos: `24 passed`.
- Suíte completa no ambiente virtual do projeto: `613 passed, 20 skipped`, sem
  falhas; permanecem os 2 avisos de depreciação preexistentes.
- A primeira tentativa com o Python global não chegou aos testes porque esse
  ambiente não possui a dependência `redis`; a execução válida foi repetida no
  ambiente virtual do projeto.
- Varredura de segredos: canário e release `PASS`.
- Cinco JSONs do pacote parseados com sucesso.
- Sintaxe do validador aprovada com Git Bash (`bash -n`).
- `git diff --check` sem erro; somente avisos de normalização LF/CRLF.

**Pendência e risco residual.**

O ciclo funcional em MariaDB 11.8.9 continua reservado ao CI Ubuntu, como
definido no briefing. Nenhum banco, API, n8n, Google Drive ou serviço real foi
acessado. Publicação só deve ocorrer depois da nova revisão e do CI verde.

### [2026-10-01] Claude — Revisão 2

**Veredito: ACEITA tecnicamente, com uma condição antes da publicação:** o CI do GitHub precisa ficar verde executando `validate_system_a_client_management.sh` contra o MariaDB descartável. Esse é o primeiro teste em que as procedures rodam de verdade; nem o Claude nem o Codex conseguiram executá-lo localmente.

Conferido pelo Claude no código (não só no relatório):
- **Item 1:** a listagem devolve `email` e `emails` como o primeiro e-mail por `e.id`, o mesmo critério da edição (`003_up.sql`, subconsultas `e_primary`); o validador testa um cliente com dois e-mails em que o primeiro por id não é o menor alfabético.
- **Item 2:** o fluxo de redefinição do portal voltou ao validador (`sp_cliente_password_reset_apply` com sucesso e reuso `invalid_or_expired`); 27 asserções de efeito com `assert_scalar`; casos de `unauthorized` em listagem e edição; negações com verificação de "nada mudou".
- **Item 3:** `BINARY LOWER(TRIM(...))` na comparação de cargo, nas duas ocorrências; a fixture tem `Admín` (deve ser negado) e `' ADMIN '` (deve ser autorizado).
- **Item 4:** token ausente não lança mais erro nos workflows de criar e editar; vai vazio à procedure, que responde `unauthorized` (401) antes de validar a entrada. As demais validações de entrada no n8n seguem como antes (comportamento preexistente).
- **Item 5 / D4:** `email_changed` e `document_changed` gravam só `request_id`, sem valor nem hash.
- **Item 6:** `verify.sql` passou a consultar colação do schema, das colunas e das tabelas, e índices.
- **Item 7:** `n8n_admin_client_list_v2_rollback.json` é idêntico ao workflow atual em `HEAD` (comparação JSON) e está inativo.
- **Item 8:** `sp_admin_cliente_set_folder` usa `sp_admin_client_authorize` com `('clientes','criar')` e mantém a regra de só vincular pasta vazia; `003_down.sql` restaura as quatro procedures.
- **D3:** exceção limitada a documento anterior nulo **e** status anterior `Lead`; e-mail sempre exige cargo administrativo.
- Suíte padrão: 613 aprovados, 20 ignorados, 0 falhas. Varredura de segredos `PASS`. `bash -n` válido. `git diff --check` limpo.

**Plano até a publicação:**
1. Usuário aceita → Claude relê o diff completo e faz o commit.
2. Usuário faz o push → Claude acompanha o CI com `gh`. Se o validador falhar, a tarefa volta ao Codex com o log.
3. Com o CI verde: consultas somente leitura de pré-publicação no phpMyAdmin (`verify.sql`, mais `SHOW GRANTS` do usuário do n8n), backup, `003_up.sql`, importação dos três workflows e teste guiado. O passo a passo vai no encerramento.
---

## 5. Encerramento

### [2026-10-01] Claude — Commit (encerramento parcial)

- Aceite do usuário: 01/10/2026 ("faça o commit").
- Diff completo conferido antes do commit: mesmos arquivos e conteúdo da Revisão 2.
- Commit da implementação: `9b2c079`.
- Pendente para concluir: push pelo usuário; CI verde com o validador MariaDB; publicação guiada no phpMyAdmin e no n8n.

### [2026-10-01] Claude — Falha no CI (primeira execução real do validador)

**Veredito: AJUSTES.** Push feito pelo usuário; o CI do commit `6b40dff` falhou na etapa `bash scripts/validate_system_a_client_management.sh`, antes de qualquer procedure rodar. Testes Python passaram; `pip-audit`, Alembic e varredura de segredos foram pulados por causa da falha.

**Log (trecho final):** `ERROR 1045 (28000): Access denied for user 'root'@'localhost' (using password: YES)`, logo após o download da imagem `mariadb:11.8.9`.

**Causa (confirmada pela leitura do script, linhas 31-41):**
- O laço de espera usa `mariadb-admin ping`. Esse comando retorna 0 sempre que o servidor está de pé, **mesmo quando a autenticação falha** (comportamento documentado do `mysqladmin`/`mariadb-admin ping`).
- A imagem oficial sobe primeiro um servidor temporário de inicialização (sem rede, antes de definir a senha do root) e depois o reinicia. O laço considerou esse servidor temporário pronto e o script seguiu cedo demais.
- Além disso, se as 60 tentativas se esgotassem, o laço terminaria sem erro.
- O defeito já existia na versão anterior do script, que nunca tinha sido executada. É a suspeita nº 5 do `cacador-de-bugs` na Revisão 1.

**Correção pedida ao Codex:**
1. Esperar pelo servidor definitivo com uma consulta real por TCP, que o servidor temporário não aceita: por exemplo, `mariadb --protocol=tcp --host=127.0.0.1 --user=root --password ← (a senha gerada) --execute='SELECT 1'` dentro do contêiner, repetindo até funcionar. Alternativa aceitável: o `healthcheck.sh --connect --innodb_initialized` da própria imagem, se confirmado na documentação da imagem.
2. Se o prazo esgotar, encerrar com mensagem clara e código diferente de zero, mostrando as últimas linhas de `docker logs` do contêiner (sem a senha).
3. Não mudar nenhuma asserção nem o SQL. A correção é só na espera.
4. Teste de ativos garantindo que o script não usa mais `ping` como critério de prontidão e que falha quando o prazo esgota.

Depois do ajuste: commit pelo Claude, push pelo usuário e nova execução do CI. A publicação continua bloqueada até o CI ficar verde.

### [2026-10-02] Codex — Resposta à falha do CI

Os ajustes solicitados após a primeira execução real do validador estão
concluídos. A tarefa retorna para revisão do Claude.

**Correção.**

- O laço de prontidão deixou de usar `mariadb-admin ping` e agora somente
  considera o banco pronto quando `SELECT 1` autentica como `root` por TCP em
  `127.0.0.1`. Assim, o servidor temporário sem rede da inicialização da imagem
  não satisfaz o critério.
- O estado começa explicitamente como não pronto. Se nenhuma das 60 tentativas
  funcionar, o script informa `MARIADB_READY_TIMEOUT`, mostra apenas as últimas
  50 linhas dos logs do contêiner e encerra com código diferente de zero.
- Nenhuma asserção funcional, migration SQL ou workflow foi alterado.
- O teste de ativos verifica a consulta TCP autenticada, proíbe o retorno ao
  `mariadb-admin`, e exige o ramo de timeout com logs e `exit 1`.

**Arquivos alterados nesta resposta.**

- `scripts/validate_system_a_client_management.sh`;
- `tests/unit/test_system_a_client_management_assets.py`;
- este arquivo e `docs/colaboracao/QUADRO.md`, somente para registrar e devolver
  o trabalho à revisão.

Nenhum arquivo foi criado e nenhuma migration foi criada ou alterada.

**Validação.**

- Testes específicos: `25 passed`.
- Suíte completa: `614 passed, 20 skipped`, com os 2 avisos de depreciação já
  existentes.
- Varredura de segredos: canário e release `PASS`.
- `bash -n scripts/validate_system_a_client_management.sh`: aprovado.
- `git diff --check`: sem erro; apenas avisos de normalização LF/CRLF.

O ciclo funcional descartável ainda precisa ser reexecutado no CI Ubuntu após
commit e push. Nenhum banco, API, n8n, Google Drive ou serviço real foi
acessado; a publicação continua bloqueada até o CI verde.

### [2026-10-02] Claude — Revisão do ajuste da espera do MariaDB

**Veredito: ACEITA.** Conferido no diff real, não só no relatório.

- Diff restrito ao laço de espera do script, a um teste novo e aos registros de colaboração. Nenhum SQL, asserção funcional, workflow ou migration alterado.
- A espera agora exige `SELECT 1` autenticado como `root` por TCP em `127.0.0.1`. O servidor temporário de inicialização da imagem roda sem rede, então não satisfaz mais o critério. O estado começa como não pronto; esgotadas as 60 tentativas, o script emite `MARIADB_READY_TIMEOUT`, mostra as últimas 50 linhas de `docker logs` (sem a senha, que só existe em variável e argumento) e sai com `exit 1`.
- `set -euo pipefail` já estava ativo; o `|| true` em `docker logs` não mascara a saída com erro.
- Final de linha: o script está como LF no índice e na cópia de trabalho (`git ls-files --eol`), então o Bash do Ubuntu não quebra.
- Reexecutado pelo Claude: testes específicos `25 passed`; suíte completa `614 passed, 20 skipped`; `bash -n` aprovado.

**Limitação registrada:** o teste novo é estático (confere o texto do script). O comportamento real da espera só é provado no CI, porque o Docker não está disponível nesta máquina. Isso é aceitável para este ajuste; o CI verde é a condição para fechar.

**Próximo passo:** "aceito" do usuário → commit pelo Claude → push pelo usuário → CI. A publicação no phpMyAdmin e no n8n continua bloqueada até o CI ficar verde.

### [2026-10-02] Claude — Commit do ajuste

- "Aceito" do usuário recebido. Diff de produção relido antes do commit: idêntico ao revisado (script +15/−3, teste +13).
- Commit único com o ajuste e estes registros (mensagem: `fix(ci): wait for authenticated TCP MariaDB before System A validation (T-0003)`).
- Pendente: push pelo usuário; CI verde; publicação guiada no phpMyAdmin e no n8n.

### [2026-10-02] Claude — Segunda execução do CI (commit `4dbca5c`, run 37019984274)

**Veredito: AJUSTES.** A correção da espera funcionou: o MariaDB ficou pronto cerca de 10 s depois do download da imagem, as migrations 001–003 foram aplicadas e as procedures rodaram. O script parou numa asserção, com a mensagem `ASSERT_SCALAR_FAILED expected=1 actual=0`, sem dizer qual consulta falhou.

**Causa (confirmada pela leitura do script e da base de teste; Docker indisponível localmente):**
- `test_base_schema.sql` insere os funcionários sem `id` explícito, então o AUTO_INCREMENT gera 1 a 12. O operador permitido é o id `3`, e o próprio script já usa `funcionario_id = 3` nas linhas 101-107.
- Três asserções de auditoria filtram por IDs derivados do sufixo do token, que não existem:
  - linha 184: `funcionario_id=1003` (deveria ser `3`): é a primeira a rodar e é a que falhou;
  - linha 224: `funcionario_id=1001` (deveria ser `1`);
  - linha 229: `funcionario_id=1000000002` (deveria ser `2`).
- As asserções anteriores que esperam `1` (linha 138, ≥ 9 negações auditadas; linha 198, pasta não vinculada) foram conferidas na procedure e devem passar. As 9 chamadas negadas passam por `sp_admin_client_authorize`, que grava o evento antes do `COMMIT`.
- O defeito vem do commit `9b2c079`. O SQL de produção (`001`–`003`) não é afetado.

**Correção pedida ao Codex:**
1. Corrigir os três IDs para os valores reais (`3`, `1`, `2`). Melhor ainda: obtê-los por consulta (`SELECT id FROM funcionarios WHERE email = '...'`) em vez de número fixo.
2. Fazer `assert_scalar` e `assert_contains` mostrarem qual verificação falhou, imprimindo a consulta ou um rótulo. Nunca imprimir a senha, que não aparece nas consultas.
3. Procurar no script outros números fixos que dependam do AUTO_INCREMENT.
4. Não mudar o SQL de produção nem o sentido de nenhuma asserção.
5. Teste de ativos: as asserções de auditoria não podem usar IDs de funcionário que não existam no seed.

Depois do ajuste: revisão pelo Claude, commit, push pelo usuário e nova execução do CI. A publicação continua bloqueada.

### [2026-10-02] Codex — Resposta à segunda falha do CI

Os ajustes pedidos após a segunda execução do CI estão concluídos. A tarefa
retorna para revisão do Claude.

**Correção.**

- Os IDs do Administrador, do Admin e do Operador permitido agora são obtidos
  da fixture por consultas ao e-mail sintético único. As três asserções de
  auditoria usam essas variáveis, não os sufixos dos tokens.
- O mesmo ID resolvido do Operador substituiu o único outro número fixo do
  script que dependia do AUTO_INCREMENT, usado para expirar e revogar a sessão.
  A busca confirmou que não resta comparação `funcionario_id = <número>` no
  validador.
- `assert_scalar` agora informa a consulta, o valor esperado e o valor obtido.
  `assert_contains` exige um rótulo por verificação e informa rótulo, trecho
  esperado e saída obtida. Nenhuma mensagem inclui a senha do banco.
- O teste de ativos comprova que os e-mails usados nas consultas existem no
  seed, que as asserções de auditoria usam IDs resolvidos, que não há filtro
  numérico fixo de funcionário e que as duas funções exibem contexto de falha.
- Nenhuma migration SQL, asserção funcional ou workflow foi alterado.

**Arquivos alterados nesta resposta.**

- `scripts/validate_system_a_client_management.sh`;
- `tests/unit/test_system_a_client_management_assets.py`;
- este arquivo e `docs/colaboracao/QUADRO.md`, somente para registrar e devolver
  o trabalho à revisão.

Nenhum arquivo foi criado e nenhuma migration foi criada ou alterada.

**Validação.**

- Testes específicos: `26 passed`.
- Suíte completa: `615 passed, 20 skipped`, com os 2 avisos de depreciação já
  existentes.
- Varredura de segredos: canário e release `PASS`.
- `bash -n scripts/validate_system_a_client_management.sh`: aprovado.
- `git diff --check`: sem erro; apenas avisos de normalização LF/CRLF.

O ciclo funcional descartável precisa ser reexecutado no CI Ubuntu após commit
e push. Nenhum banco, API, n8n, Google Drive ou serviço real foi acessado; a
publicação continua bloqueada até o CI verde.

### [2026-10-02] Claude — Revisão do ajuste dos IDs de funcionário

**Veredito: ACEITA.** Conferido no diff real.

- Os três IDs errados (`1003`, `1001`, `1000000002`) e o `3` fixo das linhas de expiração/revogação foram trocados por variáveis lidas do seed pelo e-mail sintético (`administrator_id`, `admin_id`, `operator_allowed_id`). Não sobrou `funcionario_id = <número>` no script.
- Nenhuma asserção mudou de sentido e nenhum valor esperado foi alterado. O SQL de produção (`001`–`003`), as migrations e os workflows estão intactos.
- `assert_contains` passou a exigir rótulo. Com `set -u`, uma chamada sem rótulo quebraria o script, por isso conferi: as 38 chamadas têm rótulo. `assert_scalar` mostra a consulta. Nenhuma consulta contém a senha do banco.
- Contagem final `client_action_forbidden = 17` conferida: o script tem exatamente 17 chamadas que esperam `forbidden`, cada uma gera um evento (9 no bloco inicial, 2 na edição negada, 6 nas regras D2/D3, pasta e auditor). As `unauthorized` fazem ROLLBACK e não contam.
- Reexecutado pelo Claude: testes específicos `26 passed`; suíte completa `615 passed, 20 skipped`; `bash -n` aprovado; script em LF.

**Observações não bloqueantes:**
- `assert_contains` agora imprime a saída inteira da procedure quando falha. Hoje são só dados sintéticos; se o script um dia rodar contra dados reais, isso precisa mudar.
- Se uma busca de ID voltar vazia, o script falha com erro de sintaxe SQL em vez de uma mensagem clara. Ele falha fechado, então é aceitável.

**Próximo passo:** "aceito" do usuário → commit pelo Claude → push pelo usuário → CI.

### [2026-10-02] Claude — Commit do ajuste dos IDs

- "Aceito" do usuário recebido. Diff de produção relido antes do commit: idêntico ao revisado (script +51/−46, teste +33).
- Commit único com o ajuste e estes registros (mensagem: `fix(ci): resolve seeded employee ids and label assertions in System A validator (T-0003)`).
- Pendente: push pelo usuário; CI verde; publicação guiada no phpMyAdmin e no n8n.

### [2026-10-02] Claude — CI verde (commit `7c92dea`, run 37022370184)

Primeira execução completa do validador contra o MariaDB 11.8.9 descartável. Conferido no log, não só pelo código de saída:

- testes Python: `515 passed`;
- `CLIENT_MANAGEMENT_AUTHORIZATION_TESTS=PASS`, `CLIENT_MANAGEMENT_AUDIT_TESTS=PASS`, `CLIENT_MANAGEMENT_ROLLBACK=PASS`;
- `pip-audit`: sem vulnerabilidades conhecidas;
- varredura de segredos: canário e release `PASS`.

As procedures das migrations 001–003, inclusive o rollback `003_down.sql`, foram executadas de verdade pela primeira vez. A condição técnica para publicar está cumprida.

**Próximo passo:** publicação guiada, com o usuário executando e o Claude orientando: consultas somente leitura de pré-publicação (`verify.sql` e `SHOW GRANTS` do usuário do n8n), backup, `003_up.sql` no phpMyAdmin, importação dos workflows no n8n e teste guiado, incluindo conferir se a listagem real devolve o mesmo número de clientes da tabela.
