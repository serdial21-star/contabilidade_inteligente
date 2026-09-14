# System Architecture

Inspeção local de 14/09/2026, commit `b249522` e prévia untracked. IMPLEMENTED indica código presente no escopo descrito; PARTIAL indica limites operacionais ou cobertura incompleta; PLANNED indica intenção; OUT_OF_SCOPE indica exclusão deste recorte. Não são certificados de produção. [Baseline e gates](PRODUCT_RELEASE_BASELINE.md).

## Application

IMPLEMENTED: monólito modular Python >=3.12, FastAPI e Uvicorn. `src/serdial21/main.py` expõe a aplicação composta em `bootstrap/application.py`; settings Pydantic Settings, lifespan e banco são compostos no bootstrap. Entradas HTTP ficam em `entrypoints/http/`; os módulos contêm domínio, aplicação/portas e adaptadores conforme a necessidade existente. `shared_kernel/` contém correlação e observabilidade.

PARTIAL: frontend real consiste na prévia local `app/`, `site/`, `ui/`, HTML/CSS/JavaScript nativos sem build ou framework frontend identificado. Não há `package.json`, framework SPA ou ligação dessa prévia à autenticação/API. `frontend/` e `web/` não existem. Shell autenticado e interface de produção: PLANNED. Não há cloud criada nesta fase.

## Domain Modules

Todos os caminhos abaixo são relativos a `src/serdial21/modules/`. Os nomes reais diferem do inventário conceitual de domínios; não criar pastas duplicadas para fazer os nomes coincidirem.

| Módulo real | Estado | Responsabilidade existente / limite |
| --- | --- | --- |
| `access_control` | IMPLEMENTED | Tenant, empresa, membership, CompanyAccess, papéis/permissões; domínio, serviço e persistência. |
| `identity` | IMPLEMENTED | Vínculo OIDC e ciclo de vida auditado; IdP operacional ainda pendente. |
| `audit` | IMPLEMENTED | AuditEvent, serviço, repositório, integridade e persistência. |
| `intake_documents` | IMPLEMENTED | Recebimento, evidências, lotes, validações, transformações e storage local. |
| `fiscal_documents` | IMPLEMENTED | NF-e modelo 55, parser e importador persistente; não abrange todo o fiscal. |
| `banking` | IMPLEMENTED | OFX com serviço/persistência; parser CSV configurável. |
| `chart_of_accounts` | IMPLEMENTED | Núcleo de contas/ledger em domínio puro; versões persistidas via catálogo. |
| `rules` | IMPLEMENTED | Regras/evaluations/releases determinísticos; sem conteúdo contábil padrão. |
| `mappings` | IMPLEMENTED | DE/PARA versionado de domínio; governança via catálogo. |
| `accounting` | IMPLEMENTED | Proposta, revisão, linhas, origem e pré-lançamento; autoridade oficial externa. |
| `catalog` | IMPLEMENTED | Governança DRAFT/REVIEW/PUBLISHED, snapshots e persistência de configurações. |
| `workflow` | IMPLEMENTED | Aprovação, segregação, jornada NF-e e checkpoints persistentes. |
| `operations` | IMPLEMENTED | Casos de uso da API interna, consultas e idempotência. |
| `locks` | IMPLEMENTED | AccountLock persistente, guard, autorização e auditoria. |
| `privacy` | PARTIAL | Políticas, legal hold, DSR interno e dry-run; sem destruição/endpoint público. |
| `reconciliation` | PARTIAL | Entidades e revisão de domínio; sem caso de uso/persistência operacional. |
| `integrations` | PARTIAL | Contratos, validação/readiness e conector Domínio bloqueado; sem entrega oficial. |
| `ai` | PARTIAL | Serviço de inferência, contratos e porta AIGateway; sem assistente/provedor de produção comprovado. |

Portal do cliente, tarefas/agenda completas, obrigações, billing e reporting como módulos operacionais próprios: PLANNED. Microsserviços e app mobile: OUT_OF_SCOPE.

## Application Services

IMPLEMENTED: autenticação/lifecycle, autorização, auditoria, intake, importadores NF-e/OFX, catálogo, locks, operações/idempotência e jornada. Fontes: respectivos `application/` e composição em `bootstrap/{identity,operations,nfe55,nfe_to_dominio,locks,audit}.py`. Domínio controla invariantes; serviços coordenam portas/transações. Inferência assistiva e privacidade têm as limitações acima. Não há autorização implícita para ampliar módulos.

## Persistence

IMPLEMENTED: SQLAlchemy 2.x, models/repositories em adaptadores; `bootstrap/database.py` administra engine/sessão e rollback. `bootstrap/model_registry.py` registra metadata. Alembic é a camada de migrations. Checkpoints de jornada preservam snapshots; auditoria mínima e efeitos no mesmo banco compartilham transação. Valores de precisão definida usam Decimal/NUMERIC, sem inventar arredondamento contábil.

## Database

IMPLEMENTED: driver `mysql+pymysql`, utf8mb4 e convenção UTC. Alvo MySQL compatível; [evidência existente de homologação MariaDB](MARIADB_HOMOLOGATION.md) registra MariaDB 11.8.8. SQLite é permitido apenas em `test`, não prova equivalência operacional com MariaDB. Head fonte `20260908_0012`; Runtime não consultado nesta fase. [Política forward-only](ENVIRONMENT_STRATEGY.md).

## Authentication

IMPLEMENTED: OIDC access token JWT RS256, issuer/audience/JWKS e vínculo local `(issuer, subject)`, via `identity/adapters/inbound/oidc.py` e serviços de identidade. PARTIAL operacional: provisionamento/homologação do IdP e revogação de sessão externa pendentes. Não há login funcional na prévia.

## Authorization

IMPLEMENTED: `access_control/application/services/authorization.py` revalida usuário, membership, papel e permissão. IDs não autorizam. Negação uniforme e testes em `tests/security/`, `tests/api/test_identity_security.py` e `tests/unit/test_permissions.py`. Customização futura não amplia permissões.

## Tenant Isolation

IMPLEMENTED no recorte existente: consultas e comandos escopados, tenant derivado de identidade confiável, FKs compostas e testes negativos. Evidências em `tests/integration/`, `tests/mariadb/` e `tests/architecture/`. A configuração conceitual de ambientes não substitui isolamento por tenant.

## Company Access

IMPLEMENTED: CompanyAccess vigente confrontado com a empresa selecionada. Acesso e bloqueios revalidados no efeito crítico. Onboarding/offboarding auditados; [contrato de identidade](IDENTITY_AND_TENANT_SECURITY.md).

## Audit

IMPLEMENTED: AuditEvent imutável, append-oriented, hash de integridade, ator/origem/assunto/versão/correlação e estados sanitizados. Consulta operacional resumida exige `audit.read`; não entrega before/after. [Mapa de suporte à Linha da Decisão](PRODUCT_FLOW.md) distingue dados persistidos de DTOs expostos. Logs não substituem eventos de negócio.

## Privacy

PARTIAL: [controles técnicos](PRIVACY_TECHNICAL_CONTROLS.md) persistem política, hold e workflow DSR; busca USERS autorizada, storage declarado manual e relatório apenas em memória. Retenção somente dry-run; destruição negada. Migration 0012 e aprovação jurídico-operacional continuam pendentes. Não há API pública DSR.

## AccountLock

IMPLEMENTED: `locks/`, migration 0009 e [documento de persistência](ACCOUNT_LOCK_PERSISTENCE.md). Impede efeitos críticos nos serviços cobertos, com escopo tenant/company, atomicidade e concorrência testadas. Desbloqueio não retoma automaticamente a jornada.

## NF-e

IMPLEMENTED no modelo 55: parser seguro, evidência imutável, hash/deduplicação, canônico, quarentena e jornada determinística. Fontes: `fiscal_documents/`, `intake_documents/`, `workflow/` e `tests/integration/test_nfe55_importer.py`. PARTIAL para corpus real/homologação; CT-e, NFS-e e integração fiscal oficial: OUT_OF_SCOPE do recorte implementado.

## OFX

IMPLEMENTED: parser/importação em `banking/`, persistência, preservação de sinal e identidade FITID; testes `test_ofx_regression.py`. Importar OFX não implica jornada contábil NF-e nem conciliação operacional completa. Corpus bancário real: pendente.

## Accounting Rules

IMPLEMENTED: `rules/domain/entities.py`, `mappings/domain/entities.py`, catálogo persistente e snapshots. Versão publicada imutável; correção cria nova versão; nenhuma conta/regra default é inventada. Conteúdo real depende de revisão/publicação do escritório.

## Accounting Proposal

IMPLEMENTED: domínio contábil, avaliação, proposta/revisão/hash, checkpoints de jornada e decisão humana com segregação, alçada, versão e idempotência. Aprovação autoriza o efeito permitido; não atesta escrituração externa. Interface de revisão utilizável: PLANNED.

## API

IMPLEMENTED: routers `health`, `identity`, `catalog`, `operations`, registrados em `bootstrap/application.py`. [API operacional](OPERATIONAL_API_MVP.md) é autoridade para rotas, permissões, bytes de upload, erros e decisões. Health live/ready, correlação, headers e logs sanitizados existentes. Não há endpoint de métricas nem agregação de widgets comprovada. Nova API de dashboard: PLANNED, requer levantamento de gaps posterior.

## CI

IMPLEMENTED: `.github/workflows/ci.yml`, GitHub Actions com Python 3.12, instalação de dependências, pytest unit/integration/api, pip-audit, head único e scanner fail-closed. `tests/architecture`, `tests/security` e MariaDB não estão no comando pytest desse workflow. READY significa configuração/evidência histórica; não foi verificado run remoto novo. Test framework: Pytest.

## Observability

PARTIAL: `shared_kernel/observability.py`, middleware HTTP, logs JSON sanitizados e MetricsRegistry local; [escopo atual](OBSERVABILITY_MVP.md). Coleta central, múltiplas réplicas, alert transport e métricas distribuídas pendentes.

## Backup/Recovery

PARTIAL: [runbook](BACKUP_RESTORE_RUNBOOK.md) e [ensaio histórico](BACKUP_RESTORE_EVIDENCE_20260908.md) de backup/restore MariaDB. Não é comprovação de backup atual. Agenda, recuperação de object storage, operação externa e aprovações continuam gates. Rollback de aplicação compatível e forward fix de banco; sem downgrade Runtime.

## External Integrations

PARTIAL: porta ObjectStorage com adaptador local `intake_documents/adapters/outbound/storage/local.py`; storage cloud não implementado. Conector Domínio e especificações parciais em `integrations/` e `docs/specifications/dominio/`; DOMINIO_EXPORT = BLOCKED_FOR_HOMOLOGATION. OIDC tem adaptador, IdP externo pendente. AIGateway é porta assistiva; integração Make.com, billing e provedores adicionais não comprovados, PLANNED apenas se aprovados posteriormente.
