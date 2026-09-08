# Homologação MySQL e migrations — Execução 27

Data da tentativa: 07/09/2026. Alvo formal do projeto: **MySQL 8.x
(`>=8.0,<9.0`)**, driver **PyMySQL**, charset **utf8mb4** e timestamps técnicos
normalizados para **UTC** pela aplicação.

## Configuração segura preparada

O arquivo `.env.mysql-homologation.example` fornece somente valores fictícios e
um banco dedicado `serdial21_homologation`. A credencial deve vir do ambiente
ou cofre em `.env.mysql-homologation`, que está ignorado pelo Git. Nunca usar
produção para os testes abaixo.

## Resultado da infraestrutura

Não há servidor MySQL local, `mysql`/`mysqld` não estão no PATH, `.env` não
existe e o Docker daemon não está ativo. A verificação Alembic falhou como
esperado com `RuntimeError: DATABASE_URL deve estar configurada para executar
migrations`. Portanto, nenhuma migration ou teste MySQL foi executado e não há
evidência que permita marcar o bloqueio como resolvido.

## Evidências obrigatórias

| Evidência | Resultado | Detalhe |
| --- | --- | --- |
| MySQL provisionado | FAIL | Serviço MySQL ausente; Docker daemon indisponível; nenhuma URL/credencial de homologação foi fornecida. |
| Versão homologada | FAIL | Faixa suportada formal: MySQL 8.x (`>=8.0,<9.0`); versão exata não foi observada em servidor real. |
| Alembic `base -> head` | FAIL | Não executado: `DATABASE_URL` ausente. |
| Migrations | FAIL | As oito revisions não foram aplicadas em MySQL real. |
| PK/FK | FAIL | Não inspecionadas em MySQL real. |
| FKs compostas | FAIL | Não inspecionadas em MySQL real. |
| UNIQUE | FAIL | Não inspecionadas em MySQL real. |
| Índices | FAIL | Não inspecionados em MySQL real. |
| DECIMAL | FAIL | Não inspecionado em MySQL real. |
| UTC | FAIL | `SET time_zone = '+00:00'` existe no código, mas não foi confirmado no servidor. |
| utf8mb4 | FAIL | URL e migrations o declaram, mas charset/collation não foram inspecionados em MySQL real. |
| Rollback transacional | FAIL | Não executado em MySQL real. |
| Isolamento tenant | FAIL | Não executado em MySQL real. |
| Concorrência crítica | FAIL | Idempotência, duplicidade, aprovação, locks e `AuditEvent` não foram exercitados no SGBD alvo. |
| AuditEvent | FAIL | Atomicidade e integridade não foram inspecionadas em MySQL real. |
| Testes MySQL | FAIL — 0 | Nenhuma suíte MySQL foi iniciada por ausência de infraestrutura. |

## Migrations previstas para a homologação

1. `20260903_0001_create_tenants`
2. `20260903_0002_access_control_boundary`
3. `20260904_0003_audit_events`
4. `20260904_0004_document_evidence_foundation`
5. `20260904_0005_nfe55_fiscal_documents`
6. `20260905_0006_ofx_banking`
7. `20260906_0007_workflow_pre_homologation`
8. `20260906_0008_nfe_journey_checkpoints`

## Procedimento pendente, quando o banco estiver disponível

1. Provisionar um MySQL 8.x vazio, dedicado e descartável com o banco
   `serdial21_homologation` em `utf8mb4`.
2. Guardar a URL `mysql+pymysql` exclusivamente no ambiente/cofre e copiar o
   template seguro para `.env.mysql-homologation`.
3. Carregar a configuração no processo e executar `alembic upgrade head` a
   partir de banco vazio; registrar a versão exata de `SELECT VERSION()`.
4. Inspecionar `information_schema` para PK, FK simples/compostas, UNIQUE,
   índices, `DECIMAL`, `DATETIME`, defaults e charset/collation.
5. Rodar os testes de isolamento, rollback, concorrência, idempotência,
   aprovação, locks e auditoria contra essa URL, sem remover os testes SQLite.
6. Executar downgrade somente em banco descartável e somente quando a migration
   declarar caminho seguro; não fazer downgrade destrutivo sobre histórico real.

## Comandos executados nesta tentativa

```text
where mysql
where mysqld
sc query MySQL80
sc query MySQL
docker version --format "{{.Server.Version}}"
.venv\Scripts\alembic.exe current
```

## Conclusão

**EXECUÇÃO 27 BLOCKED.** O bloqueio é exclusivamente a ausência de uma
instância MySQL 8.x de homologação acessível e de credenciais seguras. Nenhum
resultado FAIL acima indica defeito de schema; ele indica validação não
executada, que não pode ser inferida a partir do SQLite.
