# T-0009 — Onda 0: uma proposta por documento, reprocessamento explícito, correção só por estorno e anti-iframe

| Campo | Valor |
|---|---|
| Estado | EM_REVISÃO |
| Origem | ADR 0019, aceito em 05/10/2026; pesquisa A/B, seções 3.1–3.3; fila, itens 26, 27 e 6 (parte anti-iframe) |
| Sistema | Sistema B |
| Exige ADR | não (aplica o ADR 0019) |
| Exige ação do usuário | não (nenhuma publicação nesta tarefa) |

---

## 1. Briefing (Claude)

### [2026-10-05] Claude — Briefing

#### Problema

**1. A mesma NF-e gera duas propostas.** Hoje isso não tem efeito, porque não há livro nem exportação, mas passa a ter na onda 1.
- A tela envia uma `Idempotency-Key` aleatória a cada upload: `app/api-client.js:61`.
- Quando o importador devolve `IDEMPOTENT_REDELIVERY`, `prepare` cria uma nova jornada. Não há unicidade por documento (`src/serdial21/modules/workflow/application/services/nfe_to_dominio.py:115-160`); a tabela `nfe_journey_checkpoints` também não a garante (`workflow/adapters/outbound/persistence/journeys.py:19-29`).
- O teste `tests/integration/test_nfe_to_dominio_vertical.py:255-267` aceita esse comportamento.
- O `command_hash` inclui `approval_expires_at` e o período (`nfe_to_dominio.py:114`). A tela recalcula a validade todo dia (`app/app.js:479`), então repetir no dia seguinte dá conflito em vez de devolver o resultado.
- Reimportar com chave nova é hoje o **único** jeito de reprocessar uma jornada parada em `PENDING_RULE` ou `ACCOUNT_MAPPING_REQUIRED`.
- `supersede` não tem rota e recusa jornada sem revisão (`nfe_to_dominio.py:329-342`).

**2. Lançamento aprovado pode ser corrigido por nova revisão.** `JournalEntryRevision.correct()` aceita revisão `APPROVED_INTERNAL` (`src/serdial21/modules/accounting/domain/entities.py:25-27`), e o teste `tests/unit/test_pre_ledger.py:10` confirma o comportamento. Isso contraria o DL 486/1969, art. 2º, §2º, e a ITG 2000 (R1), itens 31–36: depois de aprovado, a correção é por estorno, transferência ou complemento.

**3. O B pode ser embutido em página de outro site.** `frame-ancestors 'none'` está só na `<meta>` (`app/index.html:8`), e o navegador ignora essa diretiva ali. Nem `deploy/web/Caddyfile:18-30` (`/app/*` e `/ui/*`) nem `deploy/host-caddy/Caddyfile.example` enviam o cabeçalho. A API já envia (`entrypoints/http/middleware/security_headers.py:17-21`).

#### Objetivo

No máximo uma proposta ativa por documento fiscal, garantida no banco. Reprocessamento por caminho explícito e auditado. Lançamento aprovado imutável. Páginas do B não embutíveis.

#### Escopo

**Dentro:**
1. **Separar a repetição da requisição da unicidade do efeito.**
   - A repetição com a mesma chave devolve o resultado anterior. O hash usado para detectar conflito considera só o que define o efeito: o conteúdo (sha256) e os campos contábeis do comando. Ficam de fora a validade da aprovação e outros campos que mudam a cada dia.
   - Justifique no relatório a lista exata de campos.
2. **Reserva por documento.** Migration Alembic aditiva cria uma tabela de reserva (nome a seu critério), com UNIQUE em (tenant_id, company_id, fiscal_document_id), FKs compostas para empresa e documento fiscal, e referência à jornada dona.
   - `prepare`, ao receber um documento que já tem reserva ativa, devolve a jornada existente, sem criar outra e sem conflito.
   - A reserva é liberada só por rejeição ou por `supersede`.
   - Liberação e criação ficam na mesma transação da jornada, com evento de auditoria.
   - O MySQL não tem índice parcial. Use uma coluna anulável no UNIQUE ou um registro de liberação; documente a escolha.
3. **Reprocessamento.** Novo caso de uso e rota para reprocessar jornada em `PENDING_RULE` ou `ACCOUNT_MAPPING_REQUIRED` contra o catálogo publicado vigente.
   - Mantém a mesma jornada e a mesma reserva; cria nova versão do checkpoint.
   - Permissão `journal.propose`, com versão esperada (`expected_version`), checagem de bloqueios e auditoria.
4. **Rota de `supersede`.** Com versão esperada e permissão `journal.propose`. Libera a reserva para que o documento possa ser preparado de novo.
5. **Aprovação imutável.** `correct()` deixa de aceitar revisão aprovada. Não implemente estorno nesta tarefa: isso entra com o livro em tabelas (onda 1). Ajuste o teste existente para o novo comportamento e acrescente o teste negativo.
6. **Anti-iframe.** Em `deploy/web/Caddyfile` (`/app/*` e `/ui/*`) e em `deploy/host-caddy/Caddyfile.example`:
   - cabeçalho `Content-Security-Policy` equivalente ao da `<meta>`, incluindo `frame-ancestors 'none'`;
   - `X-Frame-Options: DENY`.
   
   Mantenha a `<meta>`. Antes de alterar, confira se os testes estáticos do frontend dependem do Caddyfile.
7. **Tela.** A tela continua enviando a chave aleatória, que agora só protege a repetição da requisição. Quando a resposta indicar documento já existente, mostrar a jornada existente com a mensagem "Este documento já tem proposta" e o link para ela, em vez de "importado". Os botões "Reprocessar" (estados acima) e "Substituir" (`supersede`) só aparecem com a permissão.

**Fora:**
- livro em tabelas, número, histórico, data de entrada, estorno;
- caixa de entrada genérica;
- importador de plano de contas;
- reorganização do `app.js`;
- qualquer alteração em OFX, que já deduplica;
- publicação, deploy e banco real.

#### Referências

**Consultadas e aplicáveis:**
- DL 486/1969, art. 2º, §2º: "Os erros cometidos serão corrigidos por meio de lançamentos de estorno" (Planalto, consultado em 05/10/2026).
- ITG 2000 (R1), itens 31–36 (CFC, DOU 12/12/2014).
- W3C Content Security Policy Level 3: `frame-ancestors` não é suportada em `<meta>`.
- OWASP Clickjacking Defense Cheat Sheet.

**Documentos internos lidos:**
- `docs/adr/0019-dois-runtimes-e-organizacao-da-contabilizacao.md`;
- `docs/PESQUISA_ARQUITETURA_A_B_CONTABILIZACAO_2026-10-05.md`, seções 3.1–3.3;
- `AGENTS.md` §§6.3, 6.6, 6.7.

#### Restrições

- Migration aditiva e revisável, com upgrade e downgrade testados.
- Checkpoints de jornada continuam imutáveis: o listener que bloqueia UPDATE não pode ser contornado.
- Tenant e empresa vêm do contexto autenticado. A rota nova não revela jornada de outro tenant ou empresa: resposta neutra.
- Auditoria na mesma transação do efeito.
- Nenhum `float`.
- Hashes de revisão já emitidos continuam válidos (`nfe_to_dominio.py:65`).

#### Critérios de aceite

1. O mesmo XML enviado duas vezes, com chaves diferentes, gera **uma** jornada; a segunda resposta aponta para a primeira.
2. O mesmo XML com a mesma chave em outro dia (validade diferente) devolve a jornada existente, sem conflito.
3. Mesma chave com conteúdo diferente dá conflito.
4. Duas preparações concorrentes do mesmo documento terminam com uma única jornada; a outra recebe a existente ou um erro tratável, nunca uma segunda proposta.
5. Rejeição ou `supersede` liberam a reserva, e uma nova preparação cria nova jornada.
6. O reprocessamento de `PENDING_RULE`, depois de publicado o catálogo, chega a `PENDING_APPROVAL` na mesma jornada.
7. O reprocessamento é negado em outros estados, com período bloqueado, sem permissão e para outro tenant ou empresa (resposta neutra).
8. `correct()` sobre revisão aprovada levanta erro.
9. O Caddyfile serve `/app/` com `frame-ancestors 'none'` e `X-Frame-Options: DENY`.
10. A suíte inteira passa. Os testes de migration no MariaDB rodam no validador, ou estão documentados se ignorados.

#### Testes exigidos

- Unit e integração para os critérios 1 a 8, inclusive o teste negativo entre tenants e empresas para as duas rotas novas.
- Teste de concorrência para o critério 4, no padrão dos existentes.
- Teste de migration (upgrade/downgrade) no padrão de `tests/mariadb/`.
- Teste estático para o critério 9.
- Atualizar `test_nfe_to_dominio_vertical.py:255-267` e `test_pre_ledger.py:10` para o novo comportamento, explicando a mudança no relatório.

#### Riscos e pontos de atenção

- Jornadas duplicadas já existentes no banco do piloto: a migration não pode falhar por causa delas. Defina o que acontece; sugestão: a reserva aponta para a mais recente não rejeitada, e o relatório lista as duplicadas para decisão humana.
- `get_journey_by_fiscal_document` (`repositories.py:810-824`) passa a ter dono único. Confira os consumidores.

#### Ações do usuário

Nenhuma nesta tarefa. A publicação no VPS (migration e Caddy) vira runbook separado, depois do aceite.

---

## 2. Decisões do usuário

### [2026-10-05] Respostas registradas

- ADR 0019 aprovado.
- Piloto com os clientes de teste "Fenix teste" e "Teste T-0003" e **documentos fictícios**, ou seja, piloto sintético. As seis condições de dados reais ficam para quando entrar uma empresa real, depois da onda 1.
- Duas pessoas indicadas para a segregação. A identificação fica fora do repositório.
- Responsável pelas condições de dados reais: o proprietário.
- **Exportação ao Domínio** pelo manual público (solução 672). O golden file será produzido pelo proprietário, importando no Domínio um arquivo de teste. Tarefa futura.
- **Data contábil da NF-e de entrada = data de entrada.** O B sugere a data de recebimento no escritório, e a pessoa confirma ou corrige antes de aprovar. Entra com o livro em tabelas (onda 1).

### [2026-10-05] Aprovação

O proprietário aprovou o briefing ("t-0009 aprovado"). Estado: APROVADA. Implementação pelo Codex depois da publicação da T-0008, porque o protocolo admite uma tarefa em implementação por vez.

---

## 3. Implementação (Codex)

### [2026-10-05] Codex — Implementação entregue para revisão

**Resultado.** Foi implementada uma reserva ativa por documento fiscal, com
constraint no banco, escopo composto de tenant/empresa/documento e referência à
jornada dona. Criação e liberação compartilham a transação dos checkpoints e da
auditoria. Rejeição e substituição liberam a reserva; os demais estados a
preservam. Reenvio com outra chave retorna a jornada dona, e o reprocessamento
mantém jornada e reserva enquanto cria novos checkpoints.

**Hash do comando.** Entram exatamente `tenant_id`, `company_id`, SHA-256 do
conteúdo, `accounting_date`, `period_start` e `period_end`: eles definem escopo,
evidência e efeito contábil. Ficam fora `actor_id`, `idempotency_key`,
`approval_expires_at`, nome do arquivo e correlação, que identificam transporte,
autoria ou validade de uma aprovação futura. Assim, repetição no dia seguinte
não conflita; conteúdo ou período/data contábil diferentes com a mesma chave
continuam em conflito.

**Migration.** Criada `20261005_0017_nfe_journey_document_reservations.py`.
Como MySQL não possui índice parcial, `active_marker='ACTIVE'` participa da
UNIQUE; na liberação torna-se `NULL`. Isso preserva reservas antigas e permite
uma nova ativa. O backfill seleciona a jornada mais recente cujo último
checkpoint não é `REJECTED` nem `SUPERSEDED`; duplicatas históricas não
interrompem a migration. `T-0009-reservas-duplicadas.sql` lista as demais para
decisão humana.

**Aplicação e tela.** Foram adicionadas rotas autenticadas de `reprocess` e
`supersede`, com versão esperada, permissão `journal.propose`, escopo autenticado
e resposta neutra fora do escopo. O reprocessamento aceita somente
`PENDING_RULE`/`ACCOUNT_MAPPING_REQUIRED`, usa o catálogo vigente e revalida
bloqueios quando materializa as linhas. A tela mantém a chave aleatória,
identifica a jornada existente, mostra “Este documento já tem proposta” e só
exibe “Reprocessar”/“Substituir” com permissão. Os Caddyfiles enviam CSP com
`frame-ancestors 'none'` e `X-Frame-Options: DENY`; a meta CSP foi mantida.
`JournalEntryRevision.correct()` agora recusa revisão aprovada; estorno não foi
implementado.

**Arquivos.** Foram criados a migration 0017, seu teste MariaDB, o teste de
concorrência da reserva e a consulta de diagnóstico. Foram alterados jornada/serviço/repositório, borda operacional, API,
domínio contábil, cliente e tela web, ambos Caddyfiles, testes unitários, de
integração, API, frontend e migration, além deste registro e do quadro.

**Testes.** A suíte local sem serviços externos terminou com `665 passed`, `4
skipped` e `17 deselected`; o novo teste de rota/isolamento passou isoladamente.
O ciclo SQLite de upgrade/downgrade, o teste concorrente (uma única reserva
ativa) e o teste estático dos cabeçalhos passaram.
O teste `tests/mariadb/test_migration_0017.py` foi criado no padrão do Migration
Lab, mas não executado, pois o protocolo proíbe atuar contra banco real nesta
etapa. `git diff --check` não encontrou erros.

**Limitações e riscos.** Jornadas antigas sem os novos campos contábeis no JSON
continuam legíveis, mas não podem ser reprocessadas automaticamente; falham
fechado e exigem substituição/nova preparação. A migration não decide o destino
contábil das duplicatas históricas: reserva a mais recente elegível e gera o
relatório para decisão humana. Nenhuma publicação, deploy ou banco real foi
alterado. `.claude/settings.local.json` permaneceu não rastreado e intocado.

Estado entregue: **EM_REVISÃO**.

## 4. Revisões (Claude) e respostas (Codex)

### [2026-10-05] Claude — Revisão 1

**Veredito: AJUSTES.** São três ajustes. O restante está aceito: reserva com UNIQUE e `active_marker`, hash sem campos diários, rotas com versão esperada e escopo autenticado, `correct()` bloqueado, cabeçalhos no Caddy do web, teste de concorrência.

**Conferido:**
- suíte `tests/unit tests/integration tests/api tests/frontend`: 645 aprovados;
- `alembic heads` = `20261005_0017`;
- diff de `nfe_to_dominio.py`, `journeys.py`, migration 0017, rotas e Caddyfiles.

**Ajustes:**

1. **Jornada duplicada antiga fica presa (`nfe_to_dominio.py`, `_release_reservation`).**
   - O problema:
     - O backfill reserva só a jornada mais recente.
     - As demais duplicatas não rejeitadas, que são as listadas por `T-0009-reservas-duplicadas.sql`, não são donas de reserva.
     - Ao rejeitá-las (`record_decision` → REJECTED) ou substituí-las (`supersede`), `release_document` devolve `False` e a operação levanta `JourneyConflictError`.
     - Exatamente as duplicatas que precisam de decisão humana não podem ser rejeitadas nem substituídas.
   - Correção:
     - liberar só quando a jornada for a dona da reserva ativa;
     - se não for, seguir sem liberar e sem evento de reserva;
     - se a reserva ativa pertencer à própria jornada e o UPDATE não afetar linha, manter o conflito.
   - Testes:
     - rejeitar e substituir uma duplicata não dona funciona e não mexe na reserva da dona;
     - a dona continua liberando normalmente.

2. **Backfill inventa ator (`20261005_0017_...py`, `created_by=actor or uuid4()`).**
   - Um UUID aleatório como autor da reserva é dado fabricado (AGENTS.md §6.2 e §6.7).
   - Correção: `created_by` anulável na tabela e no model. O backfill usa `proposer_id` do snapshot quando existir; senão grava `NULL`, documentado como "reserva criada pela migration 0017".
   - Ajustar o teste da migration.

3. **CSP do proxy público sobrescreve a da API (`deploy/host-caddy/Caddyfile.example`).**
   - `header Content-Security-Policy ...` no site inteiro substitui o CSP mais restrito que a API envia (`default-src 'none'`, `security_headers.py:17`), porque `/api/*` passa pelo mesmo bloco.
   - Correção: no exemplo do proxy público, manter só `X-Frame-Options "DENY"`, que é igual ao da API. O CSP do `/app` e do `/ui` já vem do Caddy do web.
   - Atualizar o teste estático.

**Observação sem bloqueio:** `supersede` passou a recusar jornada `APPROVED` ou `BLOCKED_FOR_HOMOLOGATION`. É coerente com o ADR 0019 (depois da aprovação, só estorno). Consequência registrada: até o estorno da onda 1, uma proposta aprovada por engano não tem correção pelo sistema. Aceitável no piloto sintético.

### [2026-10-05] Codex — Resposta à Revisão 1

**Veredito sobre os achados.** Os três achados procediam e foram corrigidos sem
alterar o escopo aprovado.

1. **Duplicata histórica não dona.** `_release_reservation` agora consulta a
reserva ativa antes do UPDATE. Se outra jornada for a dona, rejeição ou
`supersede` continuam normalmente, sem liberar a reserva e sem emitir evento de
liberação. Se a própria jornada for a dona e o UPDATE não afetar uma linha, o
conflito permanece. O teste novo cria duas duplicatas históricas: uma é rejeitada
e outra substituída; ambas concluem e a reserva continua com a dona. Em seguida,
a rejeição da dona libera normalmente.

2. **Ator ausente no backfill.** `created_by` passou a ser anulável no model e
na migration. O backfill usa `proposer_id` quando presente e grava `NULL` quando
o snapshot não possui autor, documentado no código como reserva histórica criada
pela migration 0017. O teste MariaDB agora verifica explicitamente a nulabilidade
da coluna. Nenhuma identidade é fabricada.

3. **CSP do proxy público.** O exemplo do proxy de host não define mais
`Content-Security-Policy`; mantém apenas `X-Frame-Options: DENY`. Assim, ele não
sobrepõe o CSP `default-src 'none'` da API, enquanto `/app/*` e `/ui/*` continuam
recebendo seu CSP no Caddy interno. O teste estático agora exige ausência de CSP
global no host e presença de X-Frame-Options.

**Testes.** Os testes focados terminaram com `17 passed`. A mesma suíte usada na
revisão (`tests/unit tests/integration tests/api tests/frontend`) terminou com
`646 passed` e apenas os dois avisos já conhecidos de depreciação
Starlette/httpx. O teste MariaDB permanece preparado, mas não foi executado
contra banco externo. Nenhum deploy, publicação, commit ou serviço real foi
acionado. `.claude/settings.local.json` permaneceu intocado.

Estado devolvido: **EM_REVISÃO**.

### [2026-10-05] Claude — Revisão 2

**Veredito: ACEITA.**

**Os três ajustes foram conferidos no diff:**
- `_release_reservation` só libera quando a jornada é a dona;
- `created_by` anulável, sem UUID fabricado;
- o proxy público só envia `X-Frame-Options`.

**Defeito encontrado e corrigido pelo Claude:** o backfill passava `proposer_id` como **texto**, que é como o UUID fica guardado no snapshot JSON, para uma coluna `Uuid`. O SQLAlchemy falha com `AttributeError: 'str' object has no attribute 'hex'`, tanto em SQLite quanto em MySQL. Qualquer banco com jornada existente quebraria no `upgrade`. O defeito já existia na versão anterior (`actor or uuid4()`) e não era coberto por teste com dados.
- Correção: `_snapshot_actor()` converte para `UUID`; ausente ou inválido vira NULL.
- Teste: `tests/unit/test_migration_0017_backfill_actor.py`.

**Suíte:** 646 aprovados antes desta correção. Os testes da correção e de migrations passam.

**Publicação, ação do proprietário, em runbook à parte:**
- backup do banco do piloto;
- `alembic upgrade head` (0017);
- consulta `T-0009-reservas-duplicadas.sql`;
- atualização da imagem web/API e do Caddy no VPS;
- conferência dos cabeçalhos.
