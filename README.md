# Serdial21 Contabilidade Inteligente

## Phase 14 — Integrated QA + UAT

A QA integrada sintética validou os fluxos suportados de autenticação, Minha
Visão, empresas, documentos, NF-e, contabilidade, AccountLock, OFX, privacidade,
segurança, observabilidade e health/readiness. Consulte o
[plano e execução UAT](docs/qa/UAT_EXECUTION_REPORT.md).

O runtime Node/browser não está disponível neste ambiente; QA visual,
responsiva, acessibilidade e teclado exigem o
[signoff manual](docs/qa/MANUAL_UAT_CHECKLIST.md). Isso não altera `REAL DATA =
NO_GO`, revisão jurídica/contratual, IdP de produção ou migration 0012.

## Phase 13 — LGPD + Legal Gates

A prontidão técnica de privacidade foi revisada sem declarar conformidade
jurídica. O módulo existente de retenção, Legal Hold e DSR foi reutilizado; a
fronteira de empresa das ações DSR e da liberação de hold foi reforçada. O
inventário, os fluxos, a retenção, os fornecedores, os riscos e os insumos para
ROPA/RIPD e documentos jurídicos estão em
[docs/privacy](docs/privacy/PHASE_13_TECHNICAL_ASSESSMENT.md) e
[docs/legal](docs/legal/LGPD_LEGAL_REVIEW_CHECKLIST.md).

`TECHNICAL_PRIVACY_GATE = PASS` não significa conformidade legal. Os gates
jurídico e contratual permanecem pendentes de aprovação humana. Dados reais,
exposição externa, IdP de produção e execução da migration 0012 continuam
bloqueados; System A permanece adiado e a integração Domínio não está ativa.

## Phase 12 — Observability + Recovery

A aplicação agora emite logs JSON sanitizados com request/correlation IDs,
métricas de schema fechado, liveness/readiness mínimos e alertas por porta
neutra com cooldown. O tooling de backup recusa sobrescrita, registra checksum
e metadados, e um drill SQLite sintético comprova backup/restore local. Consulte
[OBSERVABILITY_ARCHITECTURE.md](docs/OBSERVABILITY_ARCHITECTURE.md),
[ALERTING_POLICY.md](docs/ALERTING_POLICY.md),
[BACKUP_RECOVERY_STRATEGY.md](docs/BACKUP_RECOVERY_STRATEGY.md),
[RECOVERY_RUNBOOK.md](docs/RECOVERY_RUNBOOK.md) e
[RECOVERY_DRILL_REPORT.md](docs/RECOVERY_DRILL_REPORT.md).

Agregação central, transporte real de alertas, storage externo criptografado e
drill MariaDB no ambiente final ainda exigem infraestrutura. Não houve conexão
com banco externo, migration, dado real, deploy ou exposição pública.

## Phase 11 — Security Infrastructure

A aplicação agora possui contrato fail-closed para homologação/produção, CORS e hosts explícitos, HSTS condicionado a HTTPS, respostas sensíveis `no-store`, limites independentes de corpo/NF-e/OFX e rate limiting por classes com porta para backend distribuído. Consulte [SECURITY_INFRASTRUCTURE_SPEC.md](docs/SECURITY_INFRASTRUCTURE_SPEC.md), [PRODUCTION_REVERSE_PROXY_SECURITY.md](docs/PRODUCTION_REVERSE_PROXY_SECURITY.md), [PRODUCTION_SECURITY_CHECKLIST.md](docs/PRODUCTION_SECURITY_CHECKLIST.md), [SECURITY_CONFIGURATION_MATRIX.md](docs/SECURITY_CONFIGURATION_MATRIX.md) e [THREAT_MODEL.md](docs/THREAT_MODEL.md).

Isso não configura IdP, TLS, rate limit distribuído ou segredos reais, não executa migrations e não autoriza exposição externa ou dados reais.

## Phase 09 — Linha da Decisão

A rastreabilidade operacional agora projeta uma linha cronológica segura sobre auditoria e estado canônico existentes para documentos, NF-e, extratos, propostas e revisões. O contrato é somente leitura, tenant/company-aware, exige acesso ao recurso e `audit.read`, minimiza atores e não expõe payload bruto. Consulte [DECISION_LINE_SPEC.md](docs/DECISION_LINE_SPEC.md), [DECISION_LINE_SECURITY.md](docs/DECISION_LINE_SECURITY.md) e [DECISION_LINE_DATA_GAPS.md](docs/DECISION_LINE_DATA_GAPS.md).

Não foi criada tabela, migration, exportação de auditoria, integração Domínio, dado real ou funcionalidade da Fase 10.

## Phase 08 — Accounting Intelligence

O módulo Contábil integra a proposta NF-e já produzida pelo motor determinístico com lista paginada, evidência, regra explicada, linhas compostas e decisão humana segura. Aprovação/rejeição reutilizam revisão/hash, segregação, AccountLock, idempotência e auditoria existentes. Catálogo, regras, contas e mappings são read-only. Consulte [ACCOUNTING_INTELLIGENCE_SPEC.md](docs/ACCOUNTING_INTELLIGENCE_SPEC.md) e [ACCOUNTING_DECISION_SECURITY.md](docs/ACCOUNTING_DECISION_SECURITY.md).

Não há contabilidade a partir de OFX, edição de proposta, posting/exportação Domínio, migration nova ou dados reais.

Fundação do produto Serdial21, construída como monólito modular orientado a
domínios. O MVP mantém o sistema contábil externo como autoridade da
escrituração oficial; o Serdial21 controla documentos processados, dados
canônicos, regras, propostas, workflow, aprovações, integrações e auditoria.

## Estado atual

Esta primeira fatia executável contém:

- autenticação OIDC por access token JWT RS256 e contexto tenant confiável;
- onboarding/offboarding auditados com revalidação de CompanyAccess, papel e
  permissão;
- catálogo operacional persistente de plano, regras, mappings e workflow, com
  versões DRAFT/REVIEW/PUBLISHED;

- aplicação FastAPI com fábrica de aplicação;
- Minha Visão operacional no shell web, com dez widgets permission-aware, cinco presets, contexto de empresas autorizadas e preferências locais seguras;
- configurações tipadas por variáveis de ambiente;
- endpoint de vivacidade;
- endpoint de prontidão do banco sem exposição de credenciais;
- correlação de requisições HTTP;
- engine e sessões SQLAlchemy com rollback transacional;
- Alembic conectado ao metadata e migration inicial de Tenant;
- fronteira de acesso com usuário, membership, empresa, estabelecimento,
  CompanyAccess, papéis e permissões atômicas;
- serviço de autorização tenant-aware com negação uniforme;
- auditoria transversal append-only, tenant-aware e com integridade;
- commit hook atômico para Tenant, Company, Membership e RoleBinding;
- fundação documental com evidência bruta imutável e deduplicação por SHA-256;
- recebimentos repetidos, lotes, itens, transformações, validações e linhagem;
- porta ObjectStorage com adaptador local fora do versionamento;
- importador seguro de NF-e modelo 55 com normalização de cabeçalho, itens,
  tributos suportados presentes, totais e envelope canônico;
- reentrega idempotente e quarentena para chave NF-e com hash divergente;
- testes automatizados da fundação.

O importador da Execução 06 trata exclusivamente NF-e modelo 55. CT-e, NFS-e e
integrações oficiais ainda não foram implementados. O catálogo operacional não
contém conteúdo contábil padrão: plano, regras, mappings e workflow reais devem
ser cadastrados, revisados e publicados pelo escritório. O IdP também deve ser
provisionado e configurado antes do deploy piloto.

## Preparação local no Windows

Requisitos: Python 3.12 ou superior e MySQL compatível com a versão que será
formalizada na decisão de infraestrutura.

    python -m venv .venv
    .\.venv\Scripts\Activate.ps1
    python -m pip install -e '.[dev]'
    Copy-Item .env.example .env

Substitua os valores de exemplo no arquivo .env. Nunca versione esse arquivo.
O driver deve permanecer mysql+pymysql e toda conexão força charset utf8mb4.
OBJECT_STORAGE_PATH define o diretório local de desenvolvimento; o valor
padrão .serdial21-storage permanece ignorado pelo Git.

## Executar

    uvicorn serdial21.main:app --reload

O endpoint inicial é:

    GET http://127.0.0.1:8000/api/v1/health/live

O readiness do banco responde sem revelar URL, usuário, host ou erro interno:

    GET http://127.0.0.1:8000/api/v1/health/ready

## Testar

    python -m pytest

## Migrações

As migrações são sempre produzidas e executadas com Alembic. Configure
DATABASE_URL no arquivo .env antes de executar:

    alembic history
    alembic upgrade head

## Documentação

- [Baseline de productização — Phase 01, inventário, arquitetura, roadmap e gates](docs/PRODUCT_RELEASE_BASELINE.md)
- [Site comercial — Phase 03, especificação e gates de pré-publicação](docs/MARKETING_SITE_SPEC.md)
- [Shell do aplicativo — Phase 04, autenticação, sessão e navegação](docs/APP_SHELL_SPEC.md)
- [Minha Visão — Phase 05, catálogo, estados, personalização e segurança](docs/MY_VIEW_SPEC.md)
- [Empresas e Central de Documentos — Phase 06](docs/CLIENTS_DOCUMENTS_SPEC.md)
- [Módulo Fiscal — Phase 07](docs/FISCAL_MODULE_SPEC.md)
- [Módulo Financeiro — Phase 07](docs/FINANCIAL_MODULE_SPEC.md)
- [Segurança Fiscal e Financeira — Phase 07](docs/FISCAL_FINANCIAL_SECURITY.md)
- [Observabilidade e operação — Phase 12](docs/OBSERVABILITY_ARCHITECTURE.md)
- [Fundação SLI/SLO — Phase 12](docs/SLO_SLI_FOUNDATION.md)
- [Resposta a incidentes — Phase 12](docs/INCIDENT_RESPONSE_RUNBOOK.md)
- [Modelo de segurança documental](docs/DOCUMENT_SECURITY_MODEL.md)
- [Mapa de fontes dos widgets](docs/DASHBOARD_DATA_MAP.md)
- [Configuração OIDC do cliente web — contrato público sem segredos](docs/OIDC_CONFIGURATION.md)
- [Instruções permanentes](AGENTS.md)
- [Baseline técnico](docs/TECHNICAL_BASELINE.md)
- [Índice da engenharia do produto](docs/engenharia-produto/00-indice-e-rastreabilidade.md)
- [Decisão da fundação inicial](docs/adr/0001-fundacao-tecnica-inicial.md)
- [Decisão da persistência MySQL](docs/adr/0002-persistencia-mysql.md)
- [Decisão da fronteira de acesso](docs/adr/0003-fronteira-acesso.md)
- [Decisão da auditoria transversal](docs/adr/0004-auditoria-transversal-inicial.md)
- [Decisão da fundação documental](docs/adr/0005-evidencia-documental-imutavel.md)
- [Decisão do importador NF-e 55](docs/adr/0006-importador-nfe55.md)
- [Identidade e segurança de tenant](docs/IDENTITY_AND_TENANT_SECURITY.md)
- [Runbook de onboarding/offboarding](docs/RUNBOOK_ONBOARDING_OFFBOARDING.md)
- [Governança do catálogo de produção](docs/PRODUCTION_CATALOG_GOVERNANCE.md)

