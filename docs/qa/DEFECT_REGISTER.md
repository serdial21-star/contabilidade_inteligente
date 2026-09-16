# Phase 14 — Registro de defeitos

## Human UAT remediation pass — 16/09/2026

O walkthrough posterior à automação registrou UAT-H01…UAT-H20; o histórico
automatizado abaixo permanece preservado. Classificação completa:
`UAT_REMEDIATION_MATRIX.md`.

| Grupo | IDs | Status após correção |
|---|---|---|
| Integridade P0 | H18, H19 | FIXED; reteste humano requerido |
| Fluxo P1 | H01, H04–H09, H12, H15, H17 | FIXED; reteste requerido |
| UX P2 | H02, H11, H13, H14, H16 | IMPLEMENTED |
| Enhancement | H03 | MULTI/FOLDER READY; ZIP DEFERRED_SECURITY_REASON |
| Domain gaps | H10, H20 | DOCUMENTED/BACKLOG; sem migration |

P0 aberto: 0. P1 aberto: 0. Os gaps de cadastro amplo não são contornados nem
autorizam dados reais.

Nenhum defeito real P0, P1, P2 ou P3 foi reproduzido na execução automatizada.
A indisponibilidade do runtime Node/browser é limitação do ambiente de QA, não
defeito da aplicação, e está registrada como bloqueio de signoff manual.

| ID | Severidade | Módulo | Descrição | Reprodução | Esperado | Atual | Causa | Correção | Teste | Status |
|---|---|---|---|---|---|---|---|---|---|---|
| — | — | — | nenhum defeito registrado | — | — | — | — | — | — | EMPTY |

Gaps aceitos não reabertos: motivo de rejeição sem schema, edição de proposta,
OFX→contabilidade, links diretos W004/W010, causalidade histórica de lock,
reconciliação privacy pós-restore, deleção DSR parcial, malware/ratelimit/IdP de
infraestrutura, Domínio e System A.
