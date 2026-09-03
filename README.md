# Serdial21 Contabilidade Inteligente

Fundação do produto Serdial21, construída como monólito modular orientado a
domínios. O MVP mantém o sistema contábil externo como autoridade da
escrituração oficial; o Serdial21 controla documentos processados, dados
canônicos, regras, propostas, workflow, aprovações, integrações e auditoria.

## Estado atual

Esta primeira fatia executável contém:

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
- testes automatizados da fundação.

As entidades de acesso da Execução 03 estão materializadas. Autenticação
externa, regras contábeis e integrações ainda não foram implementadas.

## Preparação local no Windows

Requisitos: Python 3.12 ou superior e MySQL compatível com a versão que será
formalizada na decisão de infraestrutura.

    python -m venv .venv
    .\.venv\Scripts\Activate.ps1
    python -m pip install -e '.[dev]'
    Copy-Item .env.example .env

Substitua os valores de exemplo no arquivo .env. Nunca versione esse arquivo.
O driver deve permanecer mysql+pymysql e toda conexão força charset utf8mb4.

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

