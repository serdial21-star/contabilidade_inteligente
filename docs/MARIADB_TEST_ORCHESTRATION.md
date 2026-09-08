# Orquestração da suíte MariaDB

## Estado e segurança

O único alvo autorizado é `u621451815_serdial21_hom`, mediante o opt-in
`SERDIAL21_RUN_MARIADB_HOMOLOGATION=1`, a confirmação de MariaDB 11.8.x e a
verificação de `DATABASE()` antes de qualquer operação de migration. O estado
canônico pretendido é `20260907_0009` (HEAD).

## Separação Runtime e Migration Lab

O harness possui guards distintos: `runtime_engine` aceita apenas o Runtime
Homologation e exige `SERDIAL21_RUN_MARIADB_HOMOLOGATION=1`; `migration_engine`
carrega exclusivamente `MARIADB_MIGRATION_DATABASE_URL`, exige
`SERDIAL21_RUN_MARIADB_MIGRATION_TESTS=1` e recusa o mesmo nome de database do
Runtime. Ambos validam MariaDB 11.8.x depois de conectar.

Na tentativa de pre-flight da separação, a conexão do Migration Lab foi
recusada antes de qualquer alteração de schema. Assim, a identidade do segundo
banco e sua condição descartável ainda não foram comprovadas. Nenhum downgrade
foi tentado no Runtime e nenhuma evidência de auditoria foi apagada.

## Inventário de estados

| Teste | Classe | Estado necessário | Mutação esperada | Estado final |
| --- | --- | --- | --- | --- |
| `test_preflight.py` | OTHER | HEAD ou qualquer revision | somente leitura | inalterado |
| `test_homologation.py` | MIGRATION_STATE_SPECIFIC | banco vazio/base | `base -> 0008` | HEAD após adaptação |
| `test_migration_0002_diagnosis.py` | MIGRATION_STATE_SPECIFIC | 0002 | `0002 -> 0001 -> 0002` | HEAD |
| `test_migration_0006_diagnosis.py` | MIGRATION_STATE_SPECIFIC | 0005 | `0005 -> 0006` | HEAD |
| `test_reset_to_base.py` | RESET_TEST | base sem dados de negócio | `HEAD -> base -> HEAD` | HEAD |
| `test_account_lock_*` | RUNTIME_HEAD/CONCURRENCY | HEAD | dados isolados por UUID | HEAD |

## Bloqueio atual

A tentativa de executar a suíte com opt-in comprovou que o banco já contém
evidências persistidas de homologação, incluindo locks e eventos de auditoria.
As migrations state-specific exigem downgrade através da revision 0008. Essa
revision possui proteção deliberada contra downgrade com dados. Remover esses
dados por SQL direto, especialmente `AuditEvent`, violaria tanto a proteção de
migration quanto a política append-only de auditoria.

Logo, não é seguro nem autorizado implementar uma fixture que force
`HEAD -> 0002`/`0005`/`base` nesse banco no estado atual. Uma solução futura
precisa de um banco descartável novo por execução ou de uma decisão formal de
retenção/limpeza das evidências de homologação. Não foram alteradas migrations,
guardrails, dados ou regras de negócio.

## Execução serial prevista

Migrations state-specific devem executar serialmente e restaurar HEAD em um
banco vazio controlado. Testes runtime devem apenas confirmar HEAD e usar IDs
próprios. Essa separação não é implementável com segurança enquanto o único
banco autorizado retiver dados append-only e o downgrade 0008 permanecer
protegido, como deve permanecer.
