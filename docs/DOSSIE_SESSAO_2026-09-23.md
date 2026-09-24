# Dossiê da iniciativa Sistema A + Sistema B — ponto de retomada

Documento único e autossuficiente: qualquer assistente de IA (não importa
qual) deve conseguir ler só isto, entender o estado real do trabalho e
continuar do mesmo jeito que vinha sendo feito, sem depender de memória de
conversa anterior. Reescrito em 2026-09-24 para consolidar tudo (as versões
anteriores tinham virado um log cronológico com partes já superadas).

**Nunca contém** senha, CPF, CNPJ ou nome de cliente/funcionário real — de
propósito. Se em algum momento este arquivo acumular algo assim, remova antes
de seguir.

Painel de acompanhamento (checklist vivo, com cada item marcado):
https://claude.ai/artifact/LjQX5XMa72tcDCQF7qTH36 (etapa 5 é a relevante).
Regras permanentes e não-negociáveis do projeto: `AGENTS.md` na raiz —
**leia antes de qualquer alteração de código**. Visão geral do projeto:
`docs/PROJECT_MASTER_GUIDE.md`.

---

## 1. Como retomar (5 minutos)

1. `git status -sb` e `git log --oneline -5` na raiz do repositório. Confira
   se a árvore está limpa e se `main` está sincronizada com `origin/main`
   (sem "[ahead N]"/"[behind N]"). Se houver commits não enviados, é comum —
   avise o usuário e peça para ele rodar `git push origin main` (o agente não
   consegue fazer push sozinho neste ambiente; não insista tentando).
2. Leia a seção 2 (estado atual) inteira antes de propor qualquer próximo
   passo — não assuma que algo está pendente sem checar aqui primeiro.
3. Leia a seção 8 (como este projeto deve ser conduzido) — são as regras de
   comportamento validadas nesta iniciativa, não só o AGENTS.md geral.
4. Antes de qualquer trabalho com banco de dados real: confirme o alvo (seção
   4) sem nunca imprimir a URL de conexão ou a senha em texto.
5. A pendência real mais provável agora está na seção 6. Confirme lá antes de
   perguntar ao usuário "o que fazer" — é provável que já esteja registrado.

---

## 2. Estado atual (o que já funciona, verificado)

### 2.1 Objetivo geral

Unir o Sistema A (portal administrativo do escritório Serdial21 — React +
Vite + Supabase Edge Functions + n8n + MySQL na Hostinger, construído e
mantido via Lovable) ao Sistema B (este repositório — Python 3.12/FastAPI,
motor de contabilidade inteligente, governado por `AGENTS.md`).

**Modelo de negócio decidido pelo usuário em 2026-09-24:** o Sistema B é um
complemento comercial do Sistema A (escritório contrata só A, ou A+B como
incremento), com plano de no futuro vender para **outros escritórios de
contabilidade**, não só o Serdial21. Isso é um projeto à parte, grande, ainda
**não iniciado** — o Sistema A de hoje é 100% single-tenant (confirmado por
grep no código-fonte: nenhuma coluna `tenant_id`/`escritorio_id` em
`clientes` nem `funcionarios`). Não desenhe nada assumindo multi-tenant no
Sistema A até essa reescrita ser explicitamente autorizada.

**Login único decidido**: o usuário entra pelo Sistema A; o Sistema B nunca
tem tela de login própria para uso real (só um provedor de teste local, ver
2.4). Isso está construído e testado — ver 2.5.

### 2.2 Dados reais já trazidos do Sistema A (ADR 0013)

Import **manual, offline, idempotente** (nunca automático/ao vivo — o gate do
Connect Hub, seção 3, continua bloqueando qualquer sincronização contínua):
- `scripts/import_sistema_a_companies.py` — empresas (a partir de um CSV de
  `clientes` exportado à mão). Nunca lê `senha`. CPF/CNPJ gravado só com
  dígitos. Pula `Lead`, sem documento, ou duplicado — nunca sobrescreve.
- `scripts/import_sistema_a_team.py` — equipe interna do escritório (duas
  tabelas novas, `office_team_members`/`company_team_assignments`, migration
  `20260923_0016`). Vínculo empresa→responsável só por nome exato
  normalizado — nunca por aproximação.
- Estado atual do banco `_dev` (ver seção 4): 1 tenant "Serdial21", 3
  empresas, 7 membros da equipe, 2 usuários reais provisionados
  (`funcionario:1` e `funcionario:3`).

### 2.3 Visual do Sistema B alinhado ao Sistema A

Sidebar recolhível (ícone-only), menu do usuário no rodapé da sidebar, topbar
fixo com leve desfoque — mantendo as cores oficiais do Sistema B
(azul-marinho/dourado/vermelho; decisão do usuário, não copiar o azul do
Sistema A). Sem persistência em `localStorage` (proibido por
`tests/frontend/test_app_shell.py`) — o estado de recolhido vale só na sessão
do navegador. `app/app.js`, `app/app-shell.css`, `ui/foundation.css`.

### 2.4 Provedor de login de desenvolvimento (ainda útil, não é o definitivo)

`scripts/dev_identity_provider.py` — servidor JWKS local + emissor de tokens
RS256, só para testar a API do Sistema B sem depender do Sistema A estar no
ar. Recusa rodar fora de `development`/`test`. Não decide o provedor de
identidade real de produção (isso é a Fase 11, ver pendência 6.3). Uso:
`docs/DEV_OIDC_PROVIDER.md`.

### 2.5 Ponte de login Sistema A → Sistema B — COMPLETA e verificada com clique real

Decisão registrada em `docs/adr/0014-ponte-login-sistema-a.md`: abre uma
**exceção pontual e nomeada** ao gate `NO_GO` do Connect Hub, só para esta
ponte de identidade — nada mais do Connect Hub foi liberado.

**Lado do Sistema A** (Lovable + eu, 2026-09-24):
- Duas Supabase Edge Functions no projeto `lgohzjneyvdtonpeapvd`:
  `sistema-b-jwks` (pública, publica a chave RS256) e
  `sistema-b-bridge-token` (autenticada via `x-app-token`, valida a sessão de
  funcionário e emite um token de 30 min para o Sistema B).
- Workflow n8n `[SECURITY] Validar Sessão de Funcionário`
  (`docs/integration/n8n_workflow_validar_sessao_funcionario.json`) —
  reaproveita a consulta EXATA já provada em produção no workflow de
  permissões (`API - Admin - Permissões (Funcionários) v2.2`), sem inventar
  coluna nenhuma.
- Item de menu "Contabilidade Inteligente" em
  `src/components/layout/AdminSidebar.tsx`, visível só para cargo
  administrador. Ao clicar: abre aba em branco na hora (evita bloqueio de
  pop-up), busca o token pela ponte, preenche a aba com
  `${VITE_SISTEMA_B_URL}#overview?bridge=<token>`. Nunca guarda o token.
  `VITE_SISTEMA_B_URL` hoje aponta para `http://127.0.0.1:8080/app/` — **o
  Sistema B ainda não tem endereço público real** (ver pendência 6.4).

**Lado do Sistema B** (aqui):
- `app/app.js`: `authMode: 'bridge'` lê o token de `#overview?bridge=<token>`
  (nunca de `localStorage`/`sessionStorage`), some com a URL antes de
  qualquer render, reaproveita o `bootstrapAuthenticated` já existente.
- `scripts/bootstrap_user_access.py` — provisiona usuário/participação/papel
  de leitura/acesso às empresas, idempotente, isolado por tenant, auditado.
- `scripts/start_local_real.py` — servidor local NOVO (diferente do
  `start_local.py`, que é só para a demonstração sintética) que serve os
  arquivos do site E repassa `/api/*` para a API real na mesma porta. Existe
  porque `app/index.html` tem `connect-src 'self'` de propósito (não deve
  ser enfraquecido); sem isso, o navegador bloqueia a chamada entre portas
  diferentes.

**Testado de ponta a ponta com CLIQUE REAL na tela real do Sistema A** (não
simulado, não por script de console): login no painel administrativo →
clique em "Contabilidade Inteligente" → aba nova abre o Sistema B já
autenticado, mostrando as empresas reais. Funcionou.

**Três problemas reais encontrados e corrigidos no caminho** (guardar para
não repetir o mesmo diagnóstico):
1. Supabase não recarrega segredo novo numa função já publicada sozinha —
   precisa republicar a função depois de criar/alterar um segredo.
2. O navegador tinha DUAS sessões simultâneas: `auth_token`/`client_user`
   (sessão de **cliente** do portal) e `admin_auth_token`/`admin_user`
   (sessão de **funcionário**, a que o Sistema B aceita). Fácil de testar com
   a errada sem perceber.
3. `funcionario_id` logado no teste era outro (`1`, conta genérica "Seu
   Nome") do que o esperado (`3`, "Sergio Rodrigues") — os dois foram
   cadastrados no Sistema B, sem custo.

**Decisão mantida, não revista**: `app/config.js` do Sistema B continua com
o padrão de fábrica `synthetic` (não virou `bridge`) mesmo com tudo
funcionando — porque o Sistema B só roda em `127.0.0.1` hoje; mudar o padrão
agora deixaria a demonstração inutilizável para qualquer pessoa sem o
Sistema B local. Ver pendência 6.4.

---

## 3. Limites que continuam valendo (não mexer sem nova autorização explícita)

- **Connect Hub geral: `NO_GO`.** `docs/integration/SYSTEM_A_INTEGRATION_READINESS_GATE.md`
  lista os bloqueios (contratos do n8n não congelados, sem credencial M2M
  genérica, sem confirmação de entrega, sem ambiente de homologação
  separado). A exceção do ADR 0014 é só para a ponte de login — nada de
  sincronizar cliente, documento, tarefa, honorário ou imposto entre os
  sistemas.
- **Sistema A não é multi-tenant.** Não desenhar nada assumindo isso até o
  usuário autorizar esse projeto separadamente (ver 2.1).
- **Nunca ler/gravar `senha`** de `clientes` ou `funcionarios` do Sistema A,
  em nenhum script, log ou auditoria.
- **CSP do Sistema B (`connect-src 'self'`, `frame-ancestors 'none'`) não
  deve ser enfraquecida** para resolver um problema de teste — resolver com
  arquitetura (proxy de mesma origem, nova aba em vez de iframe), como já foi
  feito em 2.5.
- **`app/config.js` do Sistema B continua com padrão `synthetic`** até o
  Sistema B ter um endereço real publicado (pendência 6.4) — não commitar
  `authMode: 'bridge'` como padrão antes disso.

---

## 4. Banco de dados (fatos, sem inventar)

- Alvo de desenvolvimento: `u621451815_serdial21_dev` (MariaDB 11.8.9,
  Hostinger, `srv1183.hstgr.io:3306`, usuário `u621451815_serdial21_app`). O
  usuário **não usa Docker**.
- Conexão em `.env` na raiz (git-ignorado). **Nunca abrir nem imprimir o
  conteúdo.** Antes de qualquer migration/import, confirmar o alvo por
  código (comparando `SELECT DATABASE()`), nunca assumindo pela URL.
- Estado atual: migration `20260923_0016` (HEAD). 1 tenant "Serdial21"
  (`5463ce7c-31b5-471d-97aa-89f043292ebb`), 3 empresas, 7 membros de equipe,
  2 usuários reais provisionados.
- **Nunca apontar nada para**: `u621451815_serdial21` (Sistema A produção),
  `_hml` (homologação antiga do A), `_hom` (auditoria imutável do B, sem
  autorização para dado real), `_mig` (laboratório descartável do B).
- CSVs reais de import ficam em `local_data/` (git-ignorado).
- SQLite só é aceito com `SERDIAL21_ENVIRONMENT=test` — nunca usar isso para
  dados reais.

---

## 5. Sistema A — fatos de referência (schema real, não inventar)

- `clientes`: `id, nome_cliente, nome_fantasia, cnpj_cpf, cnpj (UNIQUE),
  status (Ativo/Inativo/Lead), senha, codigo_sistema, id_pasta_inbox,
  id_pasta_raiz, responsavel (texto livre), whatsapp,
  inicio_prestacao_servicos, valor_contrato, vencimento_contrato, criado_em,
  aceita_notificacao_email, aceita_notificacao_whatsapp`.
- `funcionarios`: `id, nome_funcionario, email (UNIQUE), senha (SHA-256),
  cargo, telefone, status, ultimo_acesso, criado_em, atualizado_em, endereco,
  matricula, data_admissao, data_demissao, contato_emergencia, observacao`.
- `security_sessoes_funcionarios`: `token_hash` (SHA2 do token),
  `funcionario_id`, `expira_em`, `revogado_em`. Validação correta: `token_hash
  = SHA2(<token>, 256) AND expira_em > NOW() AND revogado_em IS NULL AND
  funcionarios.status = 'Ativo'` — consulta já provada, não reinventar.
- Login do Sistema A é **customizado**, não usa Supabase Auth. Existem duas
  sessões independentes no navegador: cliente do portal (`auth_token`/
  `client_user`) e funcionário/admin (`admin_auth_token`/`admin_user`).
- Código-fonte local do Sistema A (somente leitura, nunca escrever lá):
  `C:\Projetos\Sistema escritório\serdialconnect-hub-main`.
- Pendências de segurança/limpeza do próprio Sistema A (não relacionadas à
  ponte) estão nas etapas 0, 0B, 1, 2 do painel de tarefas.

---

## 6. Pendências reais (checar aqui antes de perguntar ao usuário)

1. **Trocar a senha do usuário `_app` do banco `_dev`** — apareceu uma vez em
   texto na conversa (o editor mostrou ao salvar o `.env`). Status: **não
   confirmado** se já foi trocada. Perguntar, não assumir.
2. **Endpoint e tela da equipe interna no site do Sistema B** — a tabela
   existe e está preenchida (2.2), mas não há leitura exposta na API nem na
   tela.
3. **Decidir o provedor de identidade definitivo (Fase 11)** — hoje a ponte
   (2.5) resolve o caso de uso real, mas produção de verdade (rotação de
   chave, revogação, múltiplos escritórios se/quando o pivô multi-tenant
   acontecer) é uma decisão maior, ainda em aberto.
4. **Publicar o Sistema B num endereço real** (fora de `127.0.0.1`) — hoje é
   o obstáculo concreto para qualquer pessoa além do desenvolvedor usar o
   ícone "Contabilidade Inteligente". Não iniciar sem decisão explícita do
   usuário sobre onde/como hospedar.
5. **Sistema A — padronizar CPF/CNPJ e limpar duplicatas** (pedido do
   usuário, para depois): login por e-mail faz com que CPF/CNPJ hoje não
   seja conferido; já apareceram um CPF gravado de dois jeitos e um cliente
   sem nenhum documento. Depois de corrigido lá, os scripts de import (2.2)
   são idempotentes — só entra o que faltou.

---

## 7. Comandos úteis

```powershell
# Suíte completa
.\.venv\Scripts\python.exe -m pytest -q

# Migration no Laboratório MariaDB (opt-in, nunca no banco de produção)
$env:SERDIAL21_RUN_MARIADB_MIGRATION_TESTS = "1"
.\.venv\Scripts\python.exe -m pytest tests/mariadb/test_migration_0016.py -q

# Reimportar do zero se necessário (idempotente; sempre --dry-run antes)
.\.venv\Scripts\python.exe scripts\bootstrap_tenant.py --name "Serdial21"
.\.venv\Scripts\python.exe scripts\import_sistema_a_companies.py --input local_data\clientes.csv --tenant-id <TENANT> --dry-run
.\.venv\Scripts\python.exe scripts\import_sistema_a_team.py --funcionarios local_data\funcionarios.csv --clientes local_data\clientes.csv --tenant-id <TENANT> --dry-run

# Demonstração sintética (sem banco, sem login real): dois cliques em
# INICIAR_SERDIAL21.cmd -> http://127.0.0.1:8080/app/

# Repetir o teste de login real (edite app/config.js LOCALMENTE antes, sem
# commitar: apiBaseUrl:'/api/v1', authMode:'bridge', dataMode:'real')
.\.venv\Scripts\python.exe -m uvicorn serdial21.main:app --port 8000 --host 127.0.0.1
.\.venv\Scripts\python.exe scripts\start_local_real.py --port 8080 --api-port 8000
# depois: entre no Sistema A de verdade como administrador e clique em
# "Contabilidade Inteligente" no menu lateral. Ao terminar, reverta
# app/config.js para o padrão commitado (synthetic) e encerre os dois
# servidores acima.
```

---

## 8. Como este projeto deve ser conduzido (para qualquer IA que continuar)

Isto não substitui `AGENTS.md` (leia-o primeiro, sempre) — é o que esta
iniciativa especificamente já validou funcionar bem com este usuário.

- **Verificar fatos no código/banco reais antes de decidir, nunca supor.**
  Toda vez que um "deveria funcionar assim" foi assumido sem checar, apareceu
  um bug (chave errada no navegador, coluna inventada, funcionário errado).
  Quando a dúvida é sobre o Sistema A, ler o código-fonte local (seção 5) ou
  pedir para o usuário rodar uma consulta somente-leitura — nunca adivinhar
  nome de coluna, tabela ou variável.
- **Registrar uma decisão como ADR (`docs/adr/NNNN-*.md`) antes de implementar,
  sempre que o trabalho tocar ou estender um limite que um ADR ou gate
  anterior já fixou.** Apresentar o conflito, as alternativas, e só seguir
  depois de aprovação explícita do usuário. Nunca reabrir silenciosamente um
  gate (ex.: Connect Hub `NO_GO`) mesmo que pareça conveniente.
- **Dividir pedidos grandes em fatias pequenas e testadas, com confirmação do
  usuário entre elas.** Não tentar construir tudo de uma vez quando o pedido
  é amplo (ex.: "una os sistemas" virou várias decisões e entregas
  separadas, cada uma testada antes da próxima).
- **Quando o usuário disser "me oriente" ou "você decide"**, isso autoriza
  decidir a ferramenta/mecanismo técnico — não autoriza decidir escopo de
  negócio, privacidade de dados ou reabrir um gate de segurança. Essas
  continuam exigindo pergunta explícita.
- **Nunca inventar estrutura, coluna, regra contábil ou nome de variável**
  para preencher uma lacuna — gerar pendência ou perguntar.
- **Testar de verdade antes de declarar concluído.** Uma chamada de API por
  `curl` não prova que a tela funciona; um clique real na tela real é o que
  finalmente fechou os itens desta iniciativa (2.5) depois de vários testes
  parciais que pareciam bons mas não eram o suficiente.
- **Manter este dossiê e o painel de tarefas (artifact) atualizados a cada
  entrega real** — não deixar para "depois", porque "depois" é exatamente o
  momento em que outra sessão (ou outra IA) precisa confiar neles.
- **Rodar a suíte de testes completa e checar por credencial acidental antes
  de cada commit.** Nunca commitar sem o usuário ter pedido.
- **Nunca fazer `git push`** — está bloqueado neste ambiente por decisão de
  segurança; sempre pedir para o usuário rodar `git push origin main`.
- **Nunca colar senha, token ou chave privada na conversa** — nem para
  debugar. Pedir para o usuário rodar comandos que mostram só o resultado
  (ex.: `Object.keys(localStorage)` em vez do valor de um token).

---

## 9. O que não fazer (resumo)

- Não apontar nada para `u621451815_serdial21`, `_hml`, `_hom` ou `_mig`.
- Não colar senha/token/chave privada na conversa; não abrir o `.env`.
- Não importar `senha` de nada do Sistema A; não vincular responsável por
  nome aproximado.
- Não usar `SERDIAL21_ENVIRONMENT=test` para rodar dados reais em SQLite.
- Não enfraquecer a CSP do Sistema B, `test_app_shell.py`, a lista de
  tabelas aprovadas em `test_migrations.py`, ou o gate do Connect Hub, para
  "fazer um teste passar".
- Não avançar para o resto do Connect Hub, nem para o projeto multi-tenant do
  Sistema A, sem autorização nova e explícita do usuário.
- Não commitar `app/config.js` com `authMode: 'bridge'` como padrão antes de
  o Sistema B ter um endereço real publicado (pendência 6.4).
