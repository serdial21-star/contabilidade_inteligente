# Matriz UAT contábil — corpus sintético

| ID | Source | Scenario | Expected result | Accounting | Security | Audit | Result |
|---|---|---|---|---|---|---|---|
| UAT-NFE-01 | `valid_minimal.xml` | NF-e 55 válida | regra `nfe55`; débito `1.1`; crédito `3.1`; Decimal 100.00; revisão e aprovação | balanced | tenant/role | trace completo | PASS automatizado |
| UAT-NFE-02 | mesma NF-e | reentrega idempotente | mesma jornada; nenhum efeito duplicado | unchanged | scoped | retry trace | PASS automatizado |
| UAT-NFE-03 | XML inválido | quarentena | sem proposta/aprovação | none | scoped | import trace | PASS automatizado |
| UAT-OFX-01 | OFX sintético | débito, FITID e sinal | FITID único; valor -10.00; quarentena segura quando inválido | no journal | scoped | import trace | PASS automatizado |
| UAT-LOCK-01 | NF-e válida + lock | aprovação bloqueada | sem efeito autorizado | blocked | permission/lock | event append-only | PASS automatizado |
| UAT-TENANT-01 | dois tenants sintéticos | acesso cruzado | `access denied`; configuração não vaza | isolated | tenant/company | scoped | PASS automatizado |

Corpus: fixtures sintéticas versionadas em `tests/fixtures/nfe55/` e OFX sintético
em `tests/api/test_operational_api.py`. Não há dados de cliente, credenciais ou
informações bancárias reais. `DOMINIO_EXPORT = BLOCKED_FOR_HOMOLOGATION`.

`AUTHORIZED_REAL_CORPUS_UAT = PENDING_HUMAN_AUTHORIZATION`.
