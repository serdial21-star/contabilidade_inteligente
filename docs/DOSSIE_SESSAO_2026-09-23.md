# Dossiê da sessão de 2026-09-23 — ponto de retomada

Documento para retomar o trabalho sem perder contexto. Nenhuma senha, CPF,
CNPJ ou nome de cliente/funcionário consta aqui de propósito. Painel de
acompanhamento (checklist): https://claude.ai/artifact/LjQX5XMa72tcDCQF7qTH36
(etapa 5). Regras permanentes: `AGENTS.md`. Visão geral: `PROJECT_MASTER_GUIDE.md`.

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
3. **Criar o seu usuário no B:** `users` (issuer+subject do token = os mesmos
   valores usados em `issue-token --subject ...` e `OIDC_ISSUER`),
   participação ativa no tenant, papel com permissão de leitura,
   `company_accesses` das 3 empresas; ligar cada membro da equipe ao seu
   usuário. Próximo passo recomendado.
4. **Subir a API real** (`uvicorn serdial21.main:app`) contra o `_dev`; `.env`
   já tem OIDC_ISSUER/AUDIENCE/JWKS_URL — falta só rodar `dev_identity_provider.py
   serve` em paralelo; `app/config.js` de `synthetic` para modo real; mesma
   origem ou CORS. Hoje `INICIAR_SERDIAL21.cmd` só serve os arquivos estáticos
   (dados fictícios).
5. **Endpoint e tela da equipe** (a tabela existe e está preenchida; falta a leitura).
6. **Decidir o provedor de login definitivo** (Fase 11) e como unir o login do A e do B.
7. **Sistema A — padronizar CPF/CNPJ** (pedido do usuário para depois): os
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
