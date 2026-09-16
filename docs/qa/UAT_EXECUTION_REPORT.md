# Phase 14 — Relatório de execução UAT

## Incremento operacional pós-remediação — 16/09/2026

Foram adicionados o cadastro bancário autorizado usado pelo matching OFX,
metadados persistentes de documento, filtros contábeis server-side e busca no
plano de contas. A migration aditiva `20260916_0013` preserva evidências e
checkpoints imutáveis. A evidência automatizada está registrada nos testes;
o roteiro manual foi ampliado, sem alterar o gate:

```text
HUMAN UAT: RETEST_REQUIRED
```

## HUMAN UAT REMEDIATION PASS — 16/09/2026

Analisados 20/20 achados. Corrigidos deep-link/F5, alertas, data fiscal padrão,
ownership NF-e e OFX, detalhes OFX/contábil, filtros/reset, inbox, ajuda,
timeline e widgets. Não houve migration. ZIP, metadados documentais genéricos,
Company amplo e Supplier permanecem fora desta remediação, registrados em backlog.

Os resultados automatizados originais abaixo não foram alterados. O reteste
reduzido está em `UAT_REMEDIATION_RETEST.md`.

```text
HUMAN UAT FINDINGS ANALYZED: 20 / 20
P0 OPEN: 0
P1 OPEN: 0
HUMAN UAT: RETEST_REQUIRED
```

## Resultado por cenário

| ID | Resultado | Evidência | Defeito | Notas |
|---|---|---|---|---|
| UAT-AUTH-001 | PASS | API/identity e operational smoke | — | autenticação sintética |
| UAT-DASH-001 | PASS | contratos frontend | — | render visual ainda manual |
| UAT-COMP-001 | PASS | projections/CompanyAccess | — | escopo mínimo |
| UAT-DOC-001 | PASS | API + intake persistence | — | upload sintético |
| UAT-NFE-001 | PASS | golden E2E | — | Decimal 100,00; auditoria íntegra |
| UAT-NFE-002 | PASS | idempotency/conflict | — | mesmo resultado; payload distinto 409 |
| UAT-NFE-003 | PASS | quarantine/importer | — | nenhuma proposta |
| UAT-NFE-004 | PASS | missing rule | — | `PENDING_RULE` |
| UAT-NFE-005 | PASS | ambiguous rule | — | sem seleção arbitrária |
| UAT-ACC-001 | PASS | proposal projection | — | débitos = créditos |
| UAT-ACC-002 | PASS | approve retry | — | efeito não duplicado |
| UAT-ACC-003 | PASS | reject API | — | reason continua schema gap aceito |
| UAT-LOCK-001 | PASS | persistence/unit | — | rollback e autorização cobertos |
| UAT-OFX-001 | PASS | API + regression | — | sem proposta contábil |
| UAT-OFX-002 | PASS | parser/API | — | sem persistência parcial |
| UAT-PRIV-001 | PASS | privacy focused | — | nenhuma deleção real |
| UAT-SEC-001 | PASS | IDOR/security | — | tenant/company preservados |
| UAT-OBS-001 | PASS | observability tests | — | payload sanitizado |
| UAT-HEALTH-001 | PASS | health API | — | infraestrutura simulada |
| UAT-CTX-001 | PASS | static frontend contract | — | estado descartado antes de reload |
| UAT-MOCK-001 | PASS | frontend contract parity | — | sem campo exclusivo impossível |
| UAT-ERR-001 | PASS | API/frontend safe states | — | sem stack/SQL/payload bruto |
| UAT-BROWSER-001 | BLOCKED | CUA e Node ausentes | — | checklist manual obrigatório |
| UAT-LINK-001 | BLOCKED | contrato estático parcial | — | refresh visual requer browser |

## Resumo

```text
TOTAL: 24
PASS: 22
FAIL: 0
BLOCKED: 2
P0 OPEN: 0
P1 OPEN: 0
```

Execuções intermediárias: smoke integrado `158 passed`; complemento UAT
`60 passed`; ambas sem falha. Regressão completa final: `401 passed`, `16
conditional skips`, `0 failed`, com dois avisos de depreciação de dependências.
Os bloqueios são de execução humana/browser, não defeitos comprovados do
produto.
