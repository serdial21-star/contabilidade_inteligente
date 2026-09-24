# Dossiê da sessão de 2026-09-23 — ponto de retomada

Documento para retomar o trabalho sem perder contexto. Nenhuma senha, CPF,
CNPJ ou nome de cliente/funcionário consta aqui de propósito. Painel de
acompanhamento (checklist): https://claude.ai/artifact/LjQX5XMa72tcDCQF7qTH36
(etapa 5). Regras permanentes: `AGENTS.md`. Visão geral: `PROJECT_MASTER_GUIDE.md`.

## 0. Atualização de 2026-09-24 (leia isto primeiro)

Pivô estratégico do usuário: o Sistema B passa a ser **complemento comercial
do Sistema A** (venda avulsa de A, ou A+B como incremento), vendido no futuro
para **outros escritórios de contabilidade** (não só o Serdial21) — mas o
Sistema A de hoje é 100% single-tenant (confirmado por grep: nenhuma coluna
`tenant_id`/`escritorio_id` em `clientes`/`funcionarios`). Virar multi-tenant
é um projeto à parte, muito maior, não iniciado. O login do Sistema B passa a
ser feito **pelo login do Sistema A** (login único), via uma ponte de
identidade — decisão registrada em
[ADR 0014](adr/0014-ponte-login-sistema-a.md), que abre uma **exceção pontual
e nomeada** ao gate `NO_GO` do Connect Hub (só para essa ponte de login, nada
mais). Lado do Sistema B pronto e testado ponta a ponta contra a API e o banco
`_dev` reais. Lado do Sistema A (duas Supabase Edge Functions + talvez um
workflow n8n) **ainda não implementado** — especificação completa em
[SISTEMA_A_LOGIN_BRIDGE_SPEC.md](integration/SISTEMA_A_LOGIN_BRIDGE_SPEC.md),
incluindo um achado importante: assinar o token RS256 **não pode** acontecer
num node de código do n8n (mesma trava de crypto do item 0b-3) — precisa ser
numa Edge Function (Deno). O prompt para o Lovable criar o ícone/área de
trabalho do Sistema B dentro do Sistema A fica para **depois** de a ponte
existir (decisão do usuário), não foi escrito ainda.

Trabalho novo desta atualização: `docs/adr/0014-ponte-login-sistema-a.md`,
nota de exceção em `docs/integration/SYSTEM_A_INTEGRATION_READINESS_GATE.md`,
`docs/integration/SISTEMA_A_LOGIN_BRIDGE_SPEC.md`, modo `authMode: 'bridge'`
em `app/app.js`, `scripts/bootstrap_user_access.py`, e 8 testes novos
(`tests/frontend/test_bridge_login.py`, `tests/integration/
test_bootstrap_user_access.py`). Suíte completa: 498 passed, 20 skipped.
Usuário de teste `dev-sergio` já provisionado no tenant Serdial21 do `_dev`
com acesso às 3 empresas — confirmado por chamada real a `/api/v1/identity/me`
com token do provedor de desenvolvimento.

### 0.1 Ponte concluída de ponta a ponta (mesmo dia, 24/09, mais tarde)

O Lovable construiu as duas Edge Functions do lado do Sistema A. Eu montei o
workflow `[SECURITY] Validar Sessão de Funcionário` no n8n, reaproveitando a
consulta exata já provada em produção (`API - Admin - Permissões
(Funcionários) v2.2`), sem inventar nome de coluna. Depois de resolver três
problemas reais no caminho, **o login real funcionou**: o usuário entrou pelo
Sistema A e caiu direto no Sistema B, autenticado, vendo as 3 empresas reais.

**Problemas reais encontrados e corrigidos nesta sessão (guardar para não
repetir o mesmo caminho de diagnóstico da próxima vez):**

1. **Segredo configurado, função ainda respondendo "not configured".** No
   Supabase, uma função já publicada não recarrega sozinha quando um segredo
   novo é criado/alterado — precisa ser republicada. Resolvido pedindo ao
   Lovable para republicar as duas funções.
2. **Nome errado da chave no navegador.** O primeiro teste da Lovable supôs
   `localStorage.getItem('admin_auth_token')`, mas isso corrigiu numa segunda
   tentativa: existiam DUAS sessões simultâneas no mesmo navegador —
   `auth_token`/`client_user` (sessão de **cliente**, chave `client_user` com
   `id":"25"`, o cadastro duplicado "Sergio hotmail." da importação) e
   `admin_auth_token`/`admin_user` (sessão de **funcionário**). O Sistema B só
   aceita sessão de funcionário — testar com a de cliente sempre daria
   "invalid session" (correto: são tabelas de sessão diferentes no Sistema A).
3. **Funcionário logado não era o esperado.** No painel administrativo, o
   usuário testou logado como `funcionario_id=1` ("Seu Nome", conta genérica),
   não `3` ("Sergio Rodrigues"). Os dois foram cadastrados no Sistema B
   (idempotente, sem custo cadastrar os dois).
4. **CSP bloqueando a chamada à API real.** `app/index.html` tem
   `connect-src 'self'` de propósito (não deve ser enfraquecido). Rodar o site
   numa porta (`:8080`) e a API real noutra (`:8000`) violava essa política no
   navegador. Resolvido criando `scripts/start_local_real.py` — um servidor
   local NOVO (separado do `start_local.py` sintético) que serve os mesmos
   arquivos e também repassa `/api/*` para a API real na mesma origem, sem
   mudar a política de segurança da página.

**Estado do ambiente ao terminar este teste:**
- `app/config.js` foi editado **localmente, sem commitar** (`apiBaseUrl:
  '/api/v1'`, `authMode: 'bridge'`, `dataMode: 'real'`) — revertido de volta
  ao padrão sintético commitado ao final da sessão (ver seção 0.2). Para
  repetir o teste depois, editar de novo do mesmo jeito.
- `.env` tem os endereços REAIS da ponte
  (`OIDC_ISSUER=https://lgohzjneyvdtonpeapvd.functions.supabase.co/sistema-b-bridge`,
  `OIDC_JWKS_URL=https://lgohzjneyvdtonpeapvd.supabase.co/functions/v1/sistema-b-jwks`,
  `OIDC_AUDIENCE=serdial21-sistema-b`, `CORS_ALLOWED_ORIGINS=http://127.0.0.1:8080`) —
  isso fica assim (não precisa reverter; são os valores reais e definitivos da
  ponte, não um teste descartável).
- Usuários reais provisionados no Sistema B (tenant `_dev`):
  `funcionario:1` (via issuer real) e `funcionario:3` (via issuer real; e um
  registro antigo com o emissor do provedor de teste local, inofensivo).
- Servidores locais (API real `:8000` + `scripts/start_local_real.py` `:8080`)
  encerrados ao final da sessão — reabrir com os comandos da seção 8 quando
  for testar de novo.

### 0.1.1 Ícone no Sistema A construído e testado com clique real (mesmo dia)

O Lovable adicionou o item "Contabilidade Inteligente" em
`src/components/layout/AdminSidebar.tsx` (Sistema A), visível só para
cargo administrador, dentro do grupo "Administração". Ao clicar: abre uma aba
em branco de imediato (evita bloqueio de pop-up), chama
`sistema-b-bridge-token` pelo mesmo padrão já usado no projeto
(`supabase.functions.invoke`, com `x-app-token` = `admin_auth_token`), e só
então preenche a aba com `${VITE_SISTEMA_B_URL}#overview?bridge=<token>`.
Token nunca é guardado. Endereço do Sistema B fica em `VITE_SISTEMA_B_URL`
(`.env.example`), hoje com padrão `http://127.0.0.1:8080/app/` — sem endereço
real ainda, porque o Sistema B só roda localmente.

**Testado com clique real na tela real do Sistema A** (não simulado, não pelo
console): funcionou — abriu o Sistema B autenticado, com as empresas reais.
Isso fecha o item 5-15 e completa a fatia inteira da ponte de login.

**Decisão mantida (não revista agora):** `app/config.js` do Sistema B
continua com o padrão de fábrica `synthetic` — não virou `bridge` por
padrão. Motivo: o ícone só funciona hoje com o Sistema B rodando localmente
na mesma máquina; mudar o padrão do repositório agora tornaria a demonstração
sintética inutilizável para qualquer pessoa sem o Sistema B rodando local.
Essa troca de padrão fica para quando o Sistema B tiver um endereço real
publicado — ver pendência na seção 0.2.

### 0.2 O que ficou registrado vs. o que precisa de decisão futura

- `app/config.js` **voltou ao padrão commitado** (`synthetic`) ao final desta
  sessão — o modo `bridge` não é (ainda) o padrão de fábrica do repositório,
  mesmo com o item 5-15 já pronto e testado. Motivo atualizado: falta o
  Sistema B ter um endereço real publicado; enquanto só existir em
  `127.0.0.1`, manter `synthetic` como padrão do repositório é o que preserva
  a demonstração utilizável para qualquer pessoa. Essa troca volta à mesa
  quando o Sistema B for publicado de verdade.
- `scripts/start_local_real.py` é novo e foi commitado — utilitário local
  permanente para repetir este teste sem precisar reinventar a solução do CSP.

## 1. Como retomar amanhã (5 minutos)

1. `git status -sb` e `git log --oneline -3` na raiz. Esperado: árvore limpa
   (exceto este dossiê, se ainda não commitado), `main` 7 commits à frente do
   `origin` (o push foi bloqueado — ver item 6.1).
2. Leia este arquivo e o painel (etapa 5).
3. Próximo passo recomendado: **provedor de login de desenvolvimento (OIDC de
   teste)**, depois criar o usuário, subir a API e ligar o site (seção 6).
4. Antes de qualquer trabalho com o banco: confirmar o alvo (seção 4) sem
   imprimir a URL de conexão.

## 2. Objetivo da iniciativa

Unir o Sistema A (portal/administrativo: React + Supabase Edge Functions + n8n
+ MySQL, feito com Lovable) ao Sistema B (este repositório: Python/FastAPI,
motor de contabilidade inteligente) para testar com dados reais. Pedidos do
usuário nesta sessão, em ordem: alinhar o layout do B ao do A; salvar no banco
para testes mais reais; trazer clientes/empresas do A; criar o campo "equipe"
com dados do A; abrir o site do B mostrando os clientes do banco (parcial).

## 3. O que foi feito (com commits)

| Entrega | Onde | Commit |
| --- | --- | --- |
| Visual do app alinhado ao Sistema A (sidebar recolhível, menu do usuário no rodapé, topbar com blur), mantendo as cores oficiais do B | `app/app.js`, `app/app-shell.css`, `ui/foundation.css` | `c5a63b6` |
| ADR 0013 (importação manual do Sistema A) | `docs/adr/0013-importacao-manual-dados-sistema-a.md` | `5193a7d` |
| Import de empresas (mapeamento puro + repositório + script) | `.../application/services/company_import.py`, `scripts/import_sistema_a_companies.py` | `5193a7d` |
| Equipe interna: migration `20260923_0016`, models, import, vínculo por nome exato | `alembic/versions/20260923_0016_office_team.py`, `.../services/team_import.py`, `scripts/import_sistema_a_team.py` | `5193a7d` |
| Auditoria automática das novas tabelas | `src/serdial21/bootstrap/audit.py` | `5193a7d` |
| Criar/localizar tenant | `scripts/bootstrap_tenant.py` | `5193a7d` |
| Roteiro do teste com dados reais | `docs/LOCAL_REAL_DATA_IMPORT.md` | `5193a7d` |
| Testes novos | `tests/integration/test_company_import.py`, `test_team_import.py`, `tests/mariadb/test_migration_0016.py` | `5193a7d` |

Estado dos testes ao commitar: **483 passed, 20 skipped** (os skipped exigem
MariaDB real com opt-in). A migration 0016 foi validada no Migration Lab
(`upgrade → downgrade → upgrade`). `tests/mariadb/conftest.py` passou a
esperar o HEAD `20260923_0016`; `tests/integration/test_migrations.py` ganhou as
duas tabelas novas na lista de tabelas aprovadas.

## 4. Banco de desenvolvimento (fatos)

- Alvo: banco `u621451815_serdial21_dev`, usuário `u621451815_serdial21_app`,
  host `srv1183.hstgr.io:3306`, MariaDB 11.8.9. O usuário **não usa Docker**.
- Conexão em `.env` na raiz (`SERDIAL21_ENVIRONMENT=development` + `DATABASE_URL`).
  O git ignora o arquivo. **Não abrir nem imprimir.** A senha apareceu uma vez na
  conversa (o editor mostrou a alteração do arquivo): **trocar a senha** (item 6.2).
- Estado atual: versão `20260923_0016`; 1 tenant "Serdial21"
  (`5463ce7c-31b5-471d-97aa-89f043292ebb`), 3 empresas, 7 membros da equipe,
  0 vínculos empresa↔responsável, auditoria com origem `IMPORT`.
- O `_dev` estava com um esquema antigo marcado como `0005` (faltavam índices
  únicos, `users.provider_issuer` etc.). Com aprovação e depois de verificar que
  não havia dados de negócio, foi esvaziado e reconstruído desde a base.
  Lição: comparar o esquema real com o do laboratório antes de confiar em
  `alembic_version`.
- Outros bancos Hostinger — **nunca** usar para dados reais: `u621451815_serdial21`
  (Sistema A em produção), `_hml` (homologação antiga do A), `_hom` (auditoria
  imutável, sem autorização para dados reais), `_mig` (laboratório descartável).
- As configurações recusam SQLite fora de `SERDIAL21_ENVIRONMENT=test` de
  propósito; SQLite só foi usado com dados fictícios, em ensaios.
- CSVs reais ficam em `local_data/` (ignorado pelo git): `clientes.csv`
  (7 colunas, sem senha) e `funcionarios.csv` (5 colunas, sem senha).

## 5. Decisões e regras adotadas (e por quê)

- **Import manual, offline, idempotente, com `--dry-run`** — o gate do Connect Hub
  continua `NO_GO` (trata de tráfego ao vivo); o ADR 0013 estende o limite do
  ADR 0012 com aprovação explícita do usuário. Sem conexão entre os sistemas.
- **Nunca ler `senha`** de `clientes`/`funcionarios`; também não são lidos
  endereço, telefone, contato de emergência, observação e matrícula.
- **CPF/CNPJ gravado só com dígitos (texto)**, 11 ou 14 dígitos; outro tamanho é
  pulado; dígito verificador não validado (não inventar regra). O B já compara
  documentos fiscais só por dígitos.
- **Pulados/reportados, nunca inventados:** cliente `Lead`, sem documento,
  documento duplicado, conteúdo divergente de registro já importado.
- **Vínculo empresa→responsável só por nome exato normalizado** (sem acento,
  caixa, espaços). Homônimo, inativo, inexistente ou aproximado é reportado e
  não vinculado.
- **Equipe é descritiva:** sem ligação com `users`/`tenant_memberships` até haver
  login real. A trilha de auditoria da equipe não grava nome nem e-mail.
- **Sidebar recolhida vale só na sessão** (sem `localStorage`): o teste
  `tests/frontend/test_app_shell.py` proíbe. Não afrouxar o teste.
- **Lovable não deve escrever código do Sistema B** (pilha e 72 testes estáticos
  incompatíveis). Papel futuro: tela no Sistema A que consome a API do B, depois
  de resolvida a identidade.

## 6. Pendências (ordem sugerida)

0. ~~Enviar os 7 commits ao GitHub~~ — **feito** (usuário confirmou; `git status`
   em 24/09 mostrou `main` sincronizada com `origin/main`, 0 à frente/atrás).
1. ~~Provedor de login de desenvolvimento~~ — **feito em 24/09.**
   `scripts/dev_identity_provider.py` (`init-key`, `serve`, `issue-token`):
   servidor JWKS local (`http://127.0.0.1:8090`), token RS256 com `iss/aud/sub/
   tenant_id/iat/exp`, recusa rodar fora de `development`/`test`. Testado de
   ponta a ponta com o `OidcJwtVerifier` REAL da API (mesmo código de
   produção) — verificou um token emitido pelo provedor buscando a chave via
   HTTP de verdade. `.env` ganhou `OIDC_ISSUER`, `OIDC_AUDIENCE`,
   `OIDC_JWKS_URL` apontando para o provedor local. Testes:
   `tests/unit/test_dev_identity_provider.py` (7 testes). Doc:
   `docs/DEV_OIDC_PROVIDER.md`. Suíte completa: 490 passed, 20 skipped.
2. **Trocar a senha do usuário `_app`** no hPanel e atualizar o `.env` — ainda
   pendente (confirmar se já foi feita; o `.env` mudou em disco entre sessões).
3. ~~Criar o seu usuário no B~~ — **feito em 24/09** (`scripts/
   bootstrap_user_access.py`, ver seção 0). Rodar de novo quando o `sub`/`iss`
   reais da ponte existirem.
4. **Implementar o lado do Sistema A da ponte de login** — ver
   `docs/integration/SISTEMA_A_LOGIN_BRIDGE_SPEC.md` (seção 0). Bloqueado em
   mim (só leitura no repositório do Sistema A); depende do usuário/Lovable.
5. **Ligar `app/config.js` local ao modo `bridge` para o primeiro teste visual
   pelo navegador** (ainda não feito — só testado via `curl` direto na API).
   Não commitar o `config.js` alterado; é só para teste local.
6. **Endpoint e tela da equipe** (a tabela existe e está preenchida; falta a leitura).
7. **Escrever o prompt do Lovable para o ícone/área de trabalho do Sistema B**
   dentro do Sistema A — só depois do item 4 existir (decisão do usuário).
8. **Decidir o provedor de login definitivo** (Fase 11) — agora relacionado à
   ponte do item 4, não mais um provedor OIDC genérico solto.
9. **Sistema A — padronizar CPF/CNPJ** (pedido do usuário para depois): os
   usuários entram por e-mail; o mesmo CPF aparece formatado de dois jeitos
   (duplicata 16/25), há cliente sem documento (26) e `clientes.responsavel`
   vazio em todos. Depois: reexportar CSVs e rodar os scripts (idempotentes).

## 7. Sistema A — fatos de referência

- Banco `u621451815_serdial21` (MySQL, Hostinger). `clientes`: `id, nome_cliente,
  nome_fantasia, cnpj_cpf, cnpj (UNIQUE), status (Ativo/Inativo/Lead), senha,
  codigo_sistema, id_pasta_inbox, id_pasta_raiz, responsavel (texto livre),
  whatsapp, inicio_prestacao_servicos, valor_contrato, vencimento_contrato,
  criado_em, aceita_notificacao_email, aceita_notificacao_whatsapp`.
  `funcionarios`: `id, nome_funcionario, email (UNIQUE), senha (SHA-256), cargo,
  telefone, status, ultimo_acesso, criado_em, atualizado_em, endereco, matricula,
  data_admissao, data_demissao, contato_emergencia, observacao`.
- Código-fonte local do A: `C:\Projetos\Sistema escritório\serdialconnect-hub-main`
  (somente leitura). Pendências de segurança e limpeza do A estão no painel
  (etapas 0, 0B, 1, 2).

## 8. Comandos úteis

```powershell
# Suíte completa
.\.venv\Scripts\python.exe -m pytest -q

# Migration no Laboratório (opt-in)
$env:SERDIAL21_RUN_MARIADB_MIGRATION_TESTS = "1"
.\.venv\Scripts\python.exe -m pytest tests/mariadb/test_migration_0016.py -q

# Importar (lê DATABASE_URL do .env; sempre --dry-run antes)
.\.venv\Scripts\python.exe scripts\bootstrap_tenant.py --name "Serdial21"
.\.venv\Scripts\python.exe scripts\import_sistema_a_companies.py --input local_data\clientes.csv --tenant-id <TENANT> --dry-run
.\.venv\Scripts\python.exe scripts\import_sistema_a_team.py --funcionarios local_data\funcionarios.csv --clientes local_data\clientes.csv --tenant-id <TENANT> --dry-run

# Demonstração local (dados fictícios): dois cliques em INICIAR_SERDIAL21.cmd
# -> http://127.0.0.1:8080/app/

# Repetir o teste com login real (edite app/config.js localmente antes,
# sem commitar: apiBaseUrl:'/api/v1', authMode:'bridge', dataMode:'real')
.\.venv\Scripts\python.exe -m uvicorn serdial21.main:app --port 8000 --host 127.0.0.1
.\.venv\Scripts\python.exe scripts\start_local_real.py --port 8080 --api-port 8000
# -> pegue um token real (ver seção 0.1) e abra:
# http://127.0.0.1:8080/app/#overview?bridge=SEU_TOKEN_AQUI
```

## 9. Estado do ambiente ao encerrar

- Servidor de demonstração (`127.0.0.1:8080`) iniciado em segundo plano nesta
  sessão; pode ainda estar rodando (fecha ao reiniciar ou pedindo para encerrar).
- Arquivo lixo `e 07 fiscal and financial modules"` (saída do `less` gravada por
  engano) removido.
- Memória do assistente (`~/.claude/projects/.../memory/`) atualizada:
  perfil, estilo de colaboração, esquema do Sistema A, status da unificação.
- Este dossiê e o painel podem estar mais novos que os commits: conferir
  `git status`.

## 10. O que não fazer

- Não apontar scripts para `u621451815_serdial21`, `_hml`, `_hom` ou `_mig`.
- Não colar senha em conversa nem em arquivo versionado; não abrir o `.env`.
- Não importar `senha` de nada; não vincular responsável por nome aproximado.
- Não usar `SERDIAL21_ENVIRONMENT=test` para rodar dados reais em SQLite.
- Não afrouxar `test_app_shell.py`, a lista de tabelas aprovadas ou o gate do
  Connect Hub para "passar um teste".
- Não avançar para o Connect Hub (`NO_GO`) sem autorização nova e explícita.
