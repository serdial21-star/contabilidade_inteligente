# ADR 0002 — Persistência MySQL

- Status: aceito para a Execução 02
- Data: 2026-09-03
- Escopo: configuração, conexão, sessões, health check e primeira migration

## Contexto

A fundação inicial possuía metadata SQLAlchemy e Alembic sem models. A Execução
02 determina MySQL com PyMySQL, DATABASE_URL, ambientes diferenciáveis,
pool_pre_ping, timeouts prudentes, utf8mb4, rollback e health check.

O modelo lógico aprova Tenant como raiz de isolamento. Company, memberships,
CompanyAccess, auditoria e outbox possuem dependências funcionais ainda não
implementadas e não pertencem a esta migration.

## Decisão

- Ambientes suportados: development, test e production.
- Production exige DATABASE_URL e proíbe debug.
- O driver operacional é mysql+pymysql.
- sqlite+pysqlite é aceito somente no ambiente test para testes locais rápidos;
  a homologação final de migrations continua obrigatória no MySQL suportado.
- A engine usa pool_pre_ping, rollback ao devolver conexão, reciclagem de 30
  minutos e timeouts configuráveis.
- O pool padrão é 5+5 em development, 1+0 em test e 10+20 em production.
- Toda URL MySQL recebe charset utf8mb4 e cada sessão física configura UTC.
- DATETIME é normalizado para UTC sem offset no banco e restaurado como
  datetime timezone-aware no Python; valores naive são rejeitados.
- Sessões usam autoflush desativado e não expiram objetos após commit.
- A unidade de sessão confirma no sucesso, executa rollback em falha e sempre
  fecha a sessão.
- O readiness executa SELECT 1 e retorna somente ok ou unavailable.
- O Alembic carrega explicitamente o registro de models e compara tipos e
  defaults de servidor.
- O ID de Tenant é UUID gerado pela aplicação e mapeado por SQLAlchemy Uuid;
  no MySQL atual o DDL resultante usa CHAR(32), sem significado autorizativo.
- A tabela inicial usa utf8mb4 com collation utf8mb4_unicode_ci.

## Primeira migration

A revision 20260903_0001 cria somente tenants. Os campos correspondem ao recorte
físico mínimo já aprovado: ID opaco, nome, identidade legal opcional, timezone,
moeda, status, ativação, encerramento e instante técnico de criação.

Estados possíveis, regras de transição, validação fiscal e casos de uso de
criação não são inventados nesta etapa.

## Consequências e limitações

- A aplicação inicia sem abrir conexão antecipada.
- Sem DATABASE_URL, o endpoint de vivacidade continua disponível e o readiness
  retorna 503.
- Alembic exige DATABASE_URL.
- Testes SQLite não substituem upgrade/downgrade e integração no MySQL real.
- A versão mínima suportada do MySQL ainda precisa ser formalizada e homologada.
