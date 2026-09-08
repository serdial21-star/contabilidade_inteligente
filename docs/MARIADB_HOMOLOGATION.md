# Homologação MariaDB do piloto

Data de consolidação: 08/09/2026

## Alvo

- SGBD homologado do piloto: MariaDB 11.8.x;
- versão comprovada: 11.8.8-MariaDB-log;
- driver da aplicação: `mysql+pymysql`;
- Runtime: `u621451815_serdial21_hom`;
- revision Runtime: `20260907_0009` (HEAD);
- charset de conexão: `utf8mb4`;
- timezone de sessão: UTC;
- engine das tabelas: InnoDB.

O Runtime e o Migration/Restore Lab `u621451815_serdial21_mig` são bancos
distintos, protegidos por guards de identidade. Downgrade no Runtime é proibido.

## Resultado aceito para o piloto

`DATABASE RUNTIME GATE: PASS_FOR_PILOT`

Foram aceitas as evidências consolidadas em
`docs/EXECUTION_27_CLOSURE.md`: migrations 0001–0009, FKs compostas, collation,
persistência e concorrência de AccountLock, isolamento tenant/company,
AuditEvent e rollback atômico.

## Limite da evidência

Não se afirma que todos os testes históricos/state-specific do Migration Lab
passaram. O harness ainda depende de preparação específica de revision/schema.
Essa limitação está registrada como `MIGRATION_HARNESS_STATEFUL` e foi
classificada como `DEFERRED_HARDENING`.

O caminho operacional do piloto é exclusivamente forward-only. A estratégia de
recuperação é backup + restore, nunca downgrade de schema.

## Verificação de 08/09/2026

Uma verificação read-only confirmou:

- Runtime: MariaDB 11.8.8, HEAD 0009, 33 tabelas;
- Restore Lab: MariaDB 11.8.8, HEAD 0009, 32 tabelas antes do teste de restore;
- nenhum downgrade ou DDL foi executado no Runtime.

A diferença inicial de tabelas no Lab pertence ao incidente state-specific do
harness e não altera a classificação do Runtime.

## Backup e restore da Execução 28A

Em 08/09/2026, um backup lógico transacional do Runtime foi restaurado
exclusivamente no Restore Lab. Revision, 33 tabelas, contagens completas,
estrutura, constraints, índices, InnoDB, utf8mb4, AuditEvent e AccountLock
coincidiram. A leitura ORM e o repositório tenant-aware de AccountLock passaram.

Resultado: `RESTORE TESTED`. Evidências detalhadas, sem conteúdo de negócio,
estão em `docs/BACKUP_RESTORE_EVIDENCE_20260908.md`.
