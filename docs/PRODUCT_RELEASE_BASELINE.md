# Product Release Baseline

Baseline documental de 14/09/2026 — PHASE 01. Produto: **Serdial21 Contabilidade Inteligente**, plataforma de inteligência operacional para escritórios contábeis, SaaS B2B. Slogan: **Inteligência para automatizar. Controle para decidir.**

## Estado e autoridade da evidência

| Item | Estado | Evidência / limite |
| --- | --- | --- |
| PROJECT DEVELOPMENT GATE | COMPLETE | Estado consolidado informado; Execuções 27–36 encerradas. |
| Branch / commit inspecionado | `main` / `b249522` | Snapshot local; nenhum commit/tag/publicação criado nesta fase. |
| Versão de pacote | `0.1.0` | [pyproject.toml](../pyproject.toml); não equivale a lançamento comercial. |
| SYNTHETIC PILOT | GO | [Gate final](PILOT_GO_NO_GO.md), somente interno sintético. |
| REAL DATA | NO_GO | Aprovações e pré-deploy pendentes. |
| EXTERNAL EXPOSURE | NO_GO | Infraestrutura pendente. |
| FINAL REGRESSION | 260 PASS | Evidência histórica consolidada, 0 FAIL/ERROR/SKIPPED, 2 warnings; não reexecutada. |
| PRIVACY SECURITY | 30 PASS | Evidência histórica, não nova execução. |
| ACCOUNTING UAT | 46 PASS | Sintético; não substitui accountant signoff. |
| CI | READY | Workflow presente; resultado remoto atual não consultado. |
| Alembic single head | `20260908_0012` | Cadeia 0001–0012 inspecionada nos arquivos; não é a revision verificada do Runtime. |
| MIGRATION 0012 | PRE_DEPLOY_REQUIRED | `20260908_0012_privacy_controls.py`; nenhum upgrade Runtime nesta fase. |
| DATABASE MIGRATION | FORWARD_ONLY | Recuperação/forward fix conforme runbooks; sem downgrade operacional. |
| Security / privacy | READY técnico interno / PARTIAL operacional | [Segurança](SECURITY_GATE_EXECUTION_33.md), [privacidade](PRIVACY_TECHNICAL_CONTROLS.md). |
| Operational readiness | READY interno sintético | [Runbook](OPERATIONAL_RUNBOOK.md), [drills](INCIDENT_DRILL_REPORT.md): 8 PASS / 2 PARTIAL históricos. |
| DOMINIO_EXPORT | BLOCKED_FOR_HOMOLOGATION | Sem layout homologado nem entrega oficial autorizada. |

Esta baseline referencia, sem reabrir, [Pilot Release Candidate](PILOT_RELEASE_CANDIDATE.md) e [Pilot GO/NO_GO](PILOT_GO_NO_GO.md). Trechos históricos de [Pilot Readiness](PILOT_READINESS.md) contêm contagens/revisions anteriores; o fechamento da Execução 36 é a referência consolidada. A seção E do GO/NO_GO ainda diz dependency audit UNKNOWN, enquanto a seção A e o RC registram auditoria local concluída com findings no tooling: divergência histórica registrada, sem nova certificação de dependências nesta fase.

## Inventário do repositório

Inventário pré-alteração: 715 arquivos tracked e 5 arquivos untracked não ignorados. `git diff --stat` vazio; nenhuma alteração tracked pendente. Pastas `frontend/` e `web/` ausentes. Equivalentes visuais reais: `app/`, `site/`, `ui/`.

| Caminho / cobertura | Quantidade tracked | Classificação | Conteúdo e disposição |
| --- | ---: | --- | --- |
| `src/` | 225 | PRODUCT_SOURCE | Backend Python; módulos e camadas em [arquitetura](CURRENT_SYSTEM_ARCHITECTURE.md). |
| `tests/` | 55 | TEST | unit, integration, api, architecture, security, mariadb e fixtures NF-e. |
| `alembic/` | 15 | MIGRATION | 12 revisions, `env.py`, `script.py.mako` e `versions/.gitkeep`. |
| `.github/` | 1 | CI | `workflows/ci.yml`. |
| `scripts/` | 1 | SCRIPT | `verify_release_secrets.py`. |
| `docs/` | 60 | DOCUMENTATION | ADRs, engenharia, runbooks, gates, especificações Domínio e evidências históricas. |
| `README.md`, `AGENTS.md` | 2 | DOCUMENTATION | Entrada e governança. |
| `pyproject.toml`, `requirements.lock`, `alembic.ini`, `.gitignore` | 4 | CONFIGURATION | Dependências, build, testes, migrations e exclusões. |
| `.env.example` | 1 | CONFIGURATION | Exemplo intencionalmente versionado, preservar. |
| `.env.mysql-homologation.example` | 1 | REVIEW_REQUIRED | Tracked apesar do padrão `.env.*`; revisar como exemplo de homologação antes do release. Não lido nem alterado nesta fase. |
| `.venv.broken-20260905-2/` | 350 | LOCAL_ONLY + REVIEW_REQUIRED | Virtualenv antigo já tracked; não pertence ao produto distribuível. Preservado integralmente; preparar exclusão do empacotamento em tarefa posterior revisável. |
| `app/index.html`, `app/dashboard.js`, `site/index.html`, `ui/design-system.css` | 0 (4 untracked) | REVIEW_REQUIRED | Prévia sintética HTML/CSS/JS existente; potencial fonte visual, não frontend integrado/aprovado do RC. |
| `docs/FRONTEND_VISUAL_BASE.md` | 0 (1 untracked) | DOCUMENTATION + REVIEW_REQUIRED | Descreve a prévia; identidade/tokens precisam de conciliação na Phase 02. |
| `.backups/`, `.venv/`, `.pytest_cache/`, `**/__pycache__/`, `*.pyc`, `*.egg-info/` | fora da contagem de conteúdo local ignorado | LOCAL_ONLY | Backups, ambientes e artefatos gerados; sem leitura de dumps/conteúdo sensível. |
| `.env.mariadb-migration-lab`, `.env.mysql-homologation`, demais `.env`/`.env.*` não exemplares | ignorados | LOCAL_ONLY | Configuração local; valores não inspecionados nem copiados. |
| Dumps, temporários, storage local | quando presentes | LOCAL_ONLY | Não distribuir, não remover nesta fase. |

As classificações LOCAL_ONLY têm precedência sobre a pasta para caches/artefatos gerados. REVIEW_REQUIRED é uma marca adicional de revisão, não autorização para apagar. O inventário cobre arquivos tracked, untracked e classes locais; não enumera conteúdo interno de backups/segredos. Nenhum componente é considerado implementado apenas por existir um nome de pasta.

### Git observado antes das alterações

```text
git status --short
?? app/
?? docs/FRONTEND_VISUAL_BASE.md
?? site/
?? ui/

git branch --show-current
main

git log -n 10 --oneline
b249522 execucao projeto inical completo
958ed7a execucao 31 incompleto
6556e71 execucao 27 com erro
ed51079 execucao 24
6ef9701 execucao 23 incompleto
44dfafc execucao 20 incompleto
fe92fe9 execucao 19a
7a25bd3 execucao 19
5d92aa8 execucao 18
43aef9e execucao 17

git diff --stat
(sem saída)
```

## Gates preservados

Todos os gates seguintes permanecem PENDING, sem PASS automático.

| Antes de | Gate | Responsável / evidência requerida |
| --- | --- | --- |
| Real data | AUTHORIZED_REAL_CORPUS | Dono do projeto: autorização do corpus e finalidade. |
| Real data | ACCOUNTANT_SIGNOFF | Contador: aceite do UAT/conteúdo/alçadas. |
| Real data | LEGAL_APPROVAL | Jurídico/privacidade: aprovação do escopo. |
| Real data | MIGRATION_0012_VERIFIED | Operação: backup, upgrade e verificação de schema/revision/health/smoke. |
| Real data | PRE_DEPLOY_BACKUP | Operação: backup recente, hash e recuperação validável. |
| Real data | PRIVACY_OPERATIONAL_APPROVAL | Privacidade/operação: procedimentos e cópias aprovados. |
| External exposure | CORS_ALLOWLIST | Infraestrutura: origens explícitas homologadas. |
| External exposure | HTTPS_REVERSE_PROXY | Infraestrutura: HTTPS, hosts e limites de borda validados. |
| External exposure | HSTS | Infraestrutura: política validada no proxy. |
| External exposure | DISTRIBUTED_RATE_LIMIT | Infraestrutura: controle entre réplicas validado. |
| External exposure | CENTRAL_METRICS | Operação: coleta central demonstrada. |
| External exposure | ALERT_TRANSPORT | Operação: entrega de alertas ensaiada. |
| External exposure | IDP_SESSION_REVOCATION | Identidade: revogação de sessão homologada. |

## Organização da productização

- [Arquitetura atual](CURRENT_SYSTEM_ARCHITECTURE.md) e [fluxo / Linha da Decisão](PRODUCT_FLOW.md).
- [Ambientes e migrations](ENVIRONMENT_STRATEGY.md).
- [Roadmap de 16 fases](PRODUCTIZATION_ROADMAP.md), [cronograma](PRODUCTIZATION_TIMELINE.md) e [backlog](PRODUCT_BACKLOG.md).
- [Brief de Design System](DESIGN_SYSTEM_BRIEF.md) e [brief comercial](MARKETING_SITE_BRIEF.md).

Os documentos de engenharia em `engenharia-produto/` permanecem históricos e de referência; este conjunto trata da productização. Não duplica especificações de contratos ou runbooks.

## Gate da Phase 01

| Critério | Resultado |
| --- | --- |
| REPOSITORY INVENTORY | COMPLETE |
| RELEASE BASELINE / ARCHITECTURE | DOCUMENTED |
| ENVIRONMENTS / ROADMAP / TIMELINE | DEFINED |
| BACKLOG | CREATED |
| DESIGN BRIEF / MARKETING BRIEF | READY |
| REAL DATA GATES / EXTERNAL GATES | PRESERVED |
| NO DESTRUCTIVE CHANGE | PASS |

Validação desta fase: revisão documental, links locais, cobertura dos artefatos e comparação Git. FULL REGRESSION = NOT_REQUIRED: sem alterações em código de produção, testes, dependências ou migrations. Contagens históricas não são resultados desta fase. A baseline está documentada; limpeza do pacote, revisão da prévia e gates de deploy continuam pendentes. Phase 01 PASS não aprova produção nem publica RC.
