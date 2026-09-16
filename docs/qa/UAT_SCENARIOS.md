# Phase 14 — Cenários UAT

| ID | Fluxo e aceite principal | Evidência automatizada |
|---|---|---|
| UAT-AUTH-001 | contexto autenticado, usuário/tenant e empresas autorizadas | API identity + operational authentication |
| UAT-DASH-001 | Minha Visão, W003/W004/W005/W006/W010 e estados honestos | frontend `test_my_view.py` |
| UAT-COMP-001 | lista/detalhe/CompanyAccess e projeção mínima | operational API + frontend clients |
| UAT-DOC-001 | lista, detalhe, intake, erro e entrada de rastreabilidade | operational API + document intake |
| UAT-NFE-001 | XML → validação → proposta → aprovação → auditoria/linha | operational API golden E2E |
| UAT-NFE-002 | reenvio idempotente e conflito de conteúdo | operational API + importer |
| UAT-NFE-003 | XML inválido fica em quarentena e não cria proposta | vertical/importer |
| UAT-NFE-004 | documento sem regra não fabrica proposta | vertical no-rule |
| UAT-NFE-005 | regras ambíguas não são escolhidas arbitrariamente | vertical conflict |
| UAT-ACC-001 | proposta, evidência, regra, débitos/créditos e Decimal exato | accounting projection API |
| UAT-ACC-002 | aprovação autorizada, auditada e idempotente | operational API golden E2E |
| UAT-ACC-003 | rejeição autorizada; motivo permanece schema gap | operational API rejection |
| UAT-LOCK-001 | criar/bloquear/liberar/auditar AccountLock | persistence + unit lock tests |
| UAT-OFX-001 | import, statement, transações, sinais e conta mascarada | operational API + OFX regression |
| UAT-OFX-002 | OFX inválido falha sem conjunto parcial | parser/API validation |
| UAT-PRIV-001 | DSR + Legal Hold, autorização, empresa, prioridade e audit | privacy controls/boundaries |
| UAT-SEC-001 | unauthenticated, tenant/company e IDORs | operational API + security tests |
| UAT-OBS-001 | IDs, logs/metrics fechados e falha sanitizada | observability tests |
| UAT-HEALTH-001 | liveness/readiness e dependência simulada | health API |
| UAT-CTX-001 | troca de empresa invalida estado antigo | frontend context tests |
| UAT-MOCK-001 | mock/provider respeitam shapes e estados suportados | frontend contract tests |
| UAT-ERR-001 | 401/403/404/409/413/422/429/500 seguros | API/security/frontend contract tests |
| UAT-BROWSER-001 | visual, responsivo, a11y e teclado nos breakpoints | manual; runtime indisponível |
| UAT-LINK-001 | refresh/deep link e autorização persistente | contrato parcial; browser manual |

Total: **24 cenários**, compactos e orientados aos fluxos suportados.
