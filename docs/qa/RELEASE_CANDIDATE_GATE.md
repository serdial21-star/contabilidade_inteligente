# Phase 14 — Gate técnico do release candidate

| Dimensão | Estado | Evidência/pendência |
|---|---|---|
| Build/commit base | `6583a69` | alterações Phase 14 ainda no working tree |
| testes integrados | PASS | 158 smoke + 60 complementares |
| regressão final | PASS | 401 passed, 16 conditional skips, 0 failed |
| UAT técnico | PASS | 22/24; 2 bloqueados por browser |
| browser visual | MANUAL_SIGNOFF_REQUIRED | runtime CUA/Node indisponível |
| acessibilidade/teclado | MANUAL_SIGNOFF_REQUIRED | checklist pronto |
| segurança | PASS | nenhum bypass/IDOR reproduzido |
| privacidade técnica | PASS | Phase 13 + smoke DSR/hold |
| P0/P1/P2/P3 | 0 / 0 / 0 / 0 | registro vazio |
| human UAT signoff | PENDING | não pré-aprovado |
| legal/contratual | PENDING_HUMAN_APPROVAL | independente |
| infraestrutura | PENDING | IdP, TLS, backup, observabilidade e 0012 |
| real data/exposição | NO_GO | inalterado |

Este gate não declara produção pronta. Enquanto o signoff humano estiver
pendente: `PILOT_RELEASE_GATE = WAITING_FOR_HUMAN_UAT`.
