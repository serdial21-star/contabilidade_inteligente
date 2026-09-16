# Relatório do drill de recuperação — Phase 12

## Resultado

| Campo | Evidência |
|---|---|
| Ambiente | TEST local, Windows/Python, isolado |
| Dados | duas linhas sintéticas, sem cliente |
| Tipo | backup lógico SQLite pela API nativa |
| Início/fim | execução automatizada em 15/09/2026 (horário local) |
| Destino | diretório temporário do Pytest, arquivo novo |
| Validação | SHA-256, tamanho, metadado, `integrity_check`, tabela e contagem |
| Resultado | PASS — 4 testes em 0,75 s |

O teste criou uma base sintética, gerou artefato em caminho novo, calculou
checksum, restaurou em outro destino inexistente e confirmou duas linhas. Os
casos negativos provaram rejeição de checksum corrompido, preservação de destino
existente e comando `mysqldump` sem senha/URL.

Limitações: SQLite valida a orquestração, não compatibilidade MariaDB, volume,
rede, criptografia externa, object storage, aprovação humana ou cutover. Por
isso:

```text
LOCAL_RECOVERY_DRILL: PASS
MARIADB_RECOVERY_DRILL: NOT_RUN_INFRA_REQUIRED
PRODUCTION_RPO_RTO: NOT_YET_PROVEN
```

Existe evidência histórica separada de restore MariaDB em
[BACKUP_RESTORE_EVIDENCE_20260908.md](BACKUP_RESTORE_EVIDENCE_20260908.md), mas
nenhum banco foi conectado, alterado ou migrado nesta Phase 12.
