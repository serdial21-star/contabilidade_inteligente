# Serdial21 Contabilidade Inteligente

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

