# Revisão do alvo de banco — MySQL 8 x MariaDB 11.8

Data: 07/09/2026  
Escopo: decisão arquitetural anterior à homologação. Nenhuma conexão com a
Hostinger, migration remota ou alteração de schema foi realizada.

## Situação atual

O ADR 0002 define formalmente **MySQL `>=8.0,<9.0`**, com URL e driver
`mysql+pymysql`, `utf8mb4` e UTC por sessão. A infraestrutura disponível para
o piloto informa **MariaDB 11.8.8**.

A stack fixada no lockfile é SQLAlchemy 2.0.52, PyMySQL 1.2.0 e Alembic
1.19.1. SQLAlchemy documenta MariaDB como variante suportada pelo dialeto
MySQL/MariaDB e documenta explicitamente a conexão `mysql+pymysql` para um
servidor MariaDB, com detecção da versão do servidor no primeiro connect.
Assim, o URL atualmente aceito pelo projeto continua sendo o modo correto para
a Hostinger: `mysql+pymysql://...?...`; não usar `mariadb+pymysql`, pois a
validação intencional de `AppSettings` aceita somente o primeiro e as
migrations usam opções `mysql_*`.

Fontes primárias: [dialeto SQLAlchemy MySQL/MariaDB](https://docs.sqlalchemy.org/en/21/dialects/mysql.html)
e [tipo JSON MariaDB](https://mariadb.com/docs/server/reference/data-types/string-data-types/json).

## Inventário auditado

Foram lidos o ADR 0002, `MYSQL_HOMOLOGATION.md`, revisão de engenharia,
readiness do piloto, configuração, lockfile, `alembic.ini`, `alembic/env.py`,
bootstrap de banco, as oito revisions de `20260903_0001` a `20260906_0008`,
models ORM, repositórios e testes de banco.

As migrations são SQLAlchemy/Alembic declarativas. Não há `ENUM`, coluna
gerada, `AUTO_INCREMENT`, `INSERT IGNORE`, `ON DUPLICATE KEY`, upsert
específico, `SELECT FOR UPDATE` ou função SQL proprietária. O único SQL raw é
`SELECT 1` no readiness, `SELECT COUNT(*)` no downgrade protegido da revision
0008, `CURRENT_TIMESTAMP` como default e `SET time_zone = '+00:00'` na
conexão: todos são portáveis entre os alvos no uso atual.

Há JSON em `audit_events`, workflow/exportação e checkpoints; DECIMAL nas
revisions NF-e e OFX; booleanos de acesso e itens NF-e; PKs UUID gerados pela
aplicação; e FKs simples, compostas e UNIQUE que carregam tenant/company. As
revisions 0002–0008 e os models de access control, audit, intake, fiscal,
banking e workflow são, portanto, os artefatos sensíveis à homologação.

## Compatibilidade por aspecto

| Aspecto | Classificação | Motivo e ação |
| --- | --- | --- |
| Stack SQLAlchemy + PyMySQL + Alembic | COMPATIBLE | SQLAlchemy suporta MariaDB e documenta `mysql+pymysql`; Alembic usa o engine SQLAlchemy. Confirmar conexão real com 11.8.8. |
| URL e opções de tabela | REQUIRES_TEST | `AppSettings` rejeita `mariadb+pymysql`, mas `mysql+pymysql` é o modo documentado e preserva `mysql_charset`. Testar a URL real; não há mudança necessária. |
| JSON | REQUIRES_TEST | MariaDB implementa JSON como `LONGTEXT` com `JSON_VALID`, ao contrário do JSON binário do MySQL. Não há JSON path, índice ou comparação JSON no repositório, mas serialização, validação e reflexão devem ser verificadas. |
| ENUM | COMPATIBLE | Não há uso de `ENUM`; estados são `VARCHAR`. |
| BOOLEAN | REQUIRES_TEST | O mapeamento é o convencional `TINYINT`; validar defaults `1` e round-trip booleano em MariaDB. |
| DECIMAL | REQUIRES_TEST | `Numeric(20,2)`, `(20,6)`, `(20,10)` e `(12,6)` são portáveis; inspecionar precisão/escala e round-trip de `Decimal`, sem float. |
| DATETIME/TIMESTAMP e UTC | REQUIRES_TEST | `UTCDateTime` grava UTC sem offset e o connect executa `SET time_zone='+00:00'`. Confirmar que o usuário hospedado aceita o comando e que defaults/round-trip permanecem UTC. |
| Generated columns | COMPATIBLE | Não há uso. |
| CHECK | REQUIRES_TEST | `audit_events` possui CHECK; MariaDB moderno o suporta, mas é necessário comprovar criação e rejeição no servidor alvo. |
| FKs simples | REQUIRES_TEST | São portáveis em InnoDB; inspecionar engine efetiva e enforcement na Hostinger. |
| FKs compostas | REQUIRES_TEST | São a barreira física de tenant/company. Validar todas, inclusive referências de três e quatro colunas das revisions 0004–0008. |
| PK UUID e AUTO_INCREMENT | COMPATIBLE | UUID é gerado pela aplicação; não há `AUTO_INCREMENT`. |
| UNIQUE e índices | REQUIRES_TEST | Constraints e índices declarativos são portáveis; validar criação, nomes e conflito sob concorrência. |
| Defaults | REQUIRES_TEST | Usa `CURRENT_TIMESTAMP` e defaults literais de booleano; conferir DDL refletido. |
| Collation e utf8mb4 | REQUIRES_TEST | O projeto força `utf8mb4` e a primeira migration usa `utf8mb4_unicode_ci`; confirmar charset/collation efetivos por tabela e conexão. |
| Locking e `SELECT FOR UPDATE` | COMPATIBLE | Não há SQL de lock pessimista. Isso elimina diferença de sintaxe, mas não substitui teste de corridas. |
| Transações e isolamento | REQUIRES_TEST | `session_scope` faz commit/rollback e pool reset; não há nível de isolamento explícito. Exercitar rollback e concorrência no isolamento padrão InnoDB do host. |
| Upsert / INSERT IGNORE / ON DUPLICATE | COMPATIBLE | Não há uso; a integridade depende de constraints e tratamento ORM. |
| SQL raw e funções específicas | COMPATIBLE | Apenas `SELECT 1`, `SELECT COUNT(*)`, `CURRENT_TIMESTAMP` e `SET time_zone`, sem SQL MySQL 8 exclusivo. |
| Alembic dependente de dialeto | REQUIRES_TEST | Há `mysql_charset='utf8mb4'`, compatível no modo `mysql+pymysql`; executar `base -> head`, reflexão e downgrade protegido em banco descartável MariaDB. |
| Isolamento tenant/company | REQUIRES_TEST | Autorização no serviço e FKs/UNIQUE compostas são corretas por construção, mas todos os testes existentes usam SQLite. Reexecutar negativos reais. |
| Idempotência e duplicidade | REQUIRES_TEST | Chaves UNIQUE existem, mas não há teste simultâneo contra InnoDB para provar uma única vitória e conflito de hash. |
| Aprovação, bloqueios e concorrência | REQUIRES_TEST | A regra está na aplicação; falta prova em duas sessões MariaDB para transição única e revalidação. |
| AuditEvent | REQUIRES_TEST | Append-only, CHECK e hooks estão presentes; comprovar atomicidade do efeito/evento, rollback conjunto e imutabilidade no SGBD alvo. |

Não foi encontrado item classificado como `REQUIRES_CHANGE` ou `BLOCKER` no
código atual. Isso não é uma homologação: os itens `REQUIRES_TEST` continuam
pendências obrigatórias antes de uso produtivo.

## Migrations, models e queries afetados

Todas as oito revisions entram no teste `base -> head`; as mais críticas são:

- **0002**: CompanyAccess e FKs compostas de identidade/autorização;
- **0003**: JSON, CHECK e índices do `AuditEvent`;
- **0004–0006**: cadeia de evidência, importação, NF-e/OFX, DECIMAL, UNIQUE e
  FKs compostas;
- **0007–0008**: JSON de workflow/checkpoint, FKs compostas e chaves de
  idempotência.

Os models ORM correspondentes não exigem alteração agora. As queries de
repositório usam SQLAlchemy parametrizado; a busca não encontrou SQL raw de
mutação nem extensões MySQL 8. A consulta raw de downgrade 0008 é ANSI simples.

## Testes adicionais obrigatórios

Criar uma camada MariaDB, sem retirar SQLite, que em banco descartável:

1. conecte por `mysql+pymysql`, registre `SELECT VERSION()` e execute Alembic
   `base -> head` revision por revision;
2. inspecione `information_schema` para PK, FK (inclusive compostas), UNIQUE,
   índices, `DECIMAL`, NOT NULL, defaults, JSON, charset e collation;
3. teste UTF-8 de quatro bytes, UTC, booleanos e `Decimal` nas escalas usadas;
4. repita os negativos tenant/company/CompanyAccess e as inserções
   cross-tenant que devem falhar por FK;
5. abra sessões concorrentes para idempotência/duplicidade, uma aprovação ou
   execução única, lock/revalidação e AuditEvent atômico;
6. comprove rollback de alteração de negócio e AuditEvent na mesma transação;
7. exercite downgrade apenas no banco vazio/descartável, respeitando a proteção
   de dados da revision 0008.

## Risco e decisão

O risco de adoção é **médio até a homologação**: não há bloqueador estático,
mas a cobertura de integração é predominantemente SQLite e MariaDB diverge
materialmente no armazenamento de JSON. Não há justificativa para manter MySQL
8 exclusivamente, pois não existe recurso MySQL 8 específico no produto. Não
há justificativa para dois alvos oficiais agora: isso duplicaria a matriz de
migration e concorrência, enquanto o piloto tem uma única infraestrutura.

Recomenda-se adotar **MariaDB 11.8.x** como alvo de homologação oficial do
piloto, condicionado ao conjunto de testes acima. A decisão não altera ainda o
ADR, as migrations ou `PILOT_READINESS.md`; esses artefatos só devem mudar após
evidência reproduzível de servidor real.

DATABASE DECISION: RECOMMEND_MARIADB_11_8
