# Evidência de backup e restore MariaDB — 08/09/2026

## Resultado

`BACKUP -> RESTORE LAB -> VALIDATION: RESTORE TESTED`

O Runtime permaneceu somente leitura durante backup e validação. O restore foi
executado exclusivamente em `u621451815_serdial21_mig`, após confirmação de
`SELECT DATABASE()`.

## Ferramentas

- servidor: MariaDB 11.8.8;
- `mysqldump.exe`: MySQL Community Client 8.4.9;
- `mysql.exe`: MySQL Community Client 8.4.9;
- `mariadb-dump`, `mariadb` e os clientes acima não estavam no `PATH`;
- os clientes MySQL foram usados por caminho absoluto.

## Backup

- origem: `u621451815_serdial21_hom`;
- revision: `20260907_0009`;
- timestamp UTC: `20260908T120238Z`;
- arquivo local protegido: `serdial21-runtime-20260908T120238Z.sql`;
- tamanho: 138331 bytes;
- SHA-256: `d30ed5fcc3e80d26720c1348320afc1921d2cf949cd085309f961fd5002b66e6`;
- duração: 21,229 segundos;
- resultado: PASS;
- dump ignorado pelo Git: PASS;
- referências a `alembic_version`, `audit_events` e `account_locks`: PASS;
- DDL presente e marcadores de URL/credencial ausentes: PASS.

O conteúdo do dump não foi exibido, anexado ou transmitido.

## Restore

- destino confirmado: `u621451815_serdial21_mig`;
- confirmação por `SELECT DATABASE()`: PASS;
- hash verificado antes da importação: PASS;
- duração: 18,196 segundos;
- código de saída: 0;
- resultado: PASS.

## Comparação pós-restore

| Indicador | Runtime | Restore Lab |
| --- | ---: | ---: |
| Revision Alembic | 20260907_0009 | 20260907_0009 |
| Tabelas | 33 | 33 |
| Tenants | 16 | 16 |
| Companies | 28 | 28 |
| AuditEvents | 100 | 100 |
| AccountLocks | 6 | 6 |
| PKs | 33 | 33 |
| FKs | 56 | 56 |
| FKs compostas | 49 | 49 |
| UNIQUE | 40 | 40 |
| CHECK | 8 | 8 |
| Índices | 127 | 127 |
| Tabelas não InnoDB | 0 | 0 |
| Tabelas fora de utf8mb4 | 0 | 0 |

A assinatura read-only de tabelas, colunas, constraints e índices coincidiu. As
contagens de todas as 33 tabelas também coincidiram.

## Integridade da aplicação

- leitura ORM de AuditEvent e payload JSON: PASS;
- leitura ORM de AccountLock: PASS;
- leitura de AccountLock via repositório tenant-aware: PASS;
- preservação de `scope_fingerprint`, `active_marker` e status: PASS;
- teste automatizado: 1 aprovado em 17,21 segundos.

Nenhum AuditEvent ou AccountLock restaurado foi modificado.

## Objetivos técnicos

- RPO alvo do piloto: 24 horas;
- RTO alvo do piloto: 4 horas;
- backup + restore medido: menos de 1 minuto no volume atual, sem incluir
  aprovação humana, transferência, investigação ou cutover.

Esses valores são objetivos técnicos, não SLA contratual.

## Proteção do Runtime

Após o restore, o Runtime permaneceu em HEAD 0009 com 33 tabelas e contagens
iguais às capturadas para validação. Não houve DROP, TRUNCATE, DELETE de
preparação, downgrade, alteração de schema ou restore no Runtime.
