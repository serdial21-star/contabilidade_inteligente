# Pilot Release Candidate

## Escopo permitido

Este release candidate e destinado somente ao piloto interno sintetico:
tenant/company de teste, NF-e e OFX sinteticos, catalogo persistido, proposta,
revisao/aprovacao, AccountLock, DSR tecnico, AuditEvent e API operacional
interna autenticada.

## Capacidades e evidencias

| Area | Estado | Evidencia consolidada |
| --- | --- | --- |
| Database/persistence | READY | MariaDB homologado, isolamento tenant/company, AccountLock, AuditEvent e backup/restore documentado. |
| Auth/security | READY tecnico | OIDC e AuthorizationService; privacy default-deny e privacy security com 30 PASS historicos. |
| Privacy | READY tecnico interno | Legal Hold, DSR search/report in-memory e retencao dry-run; destruicao negada. |
| Accounting | READY sintetico | corpus golden, catalogo persistido e UAT anterior: 46 PASS / 0 FAIL. |
| Operations | READY interno | deploy/rollback, lifecycle, secret rotation e drills: 8 PASS / 2 PARTIAL / 0 FAIL. |

## Capacidades excluidas

- dados pessoais, fiscais ou bancarios reais;
- exportacao oficial Dominio (`BLOCKED_FOR_HOMOLOGATION`);
- exposicao publica;
- retention destrutiva, delecao ou anonimizacao;
- migration/downgrade no Runtime fora de janela aprovada.

## Database e migration

Politica de banco: `FORWARD_ONLY`. A migration
`20260908_0012_privacy_controls` e `PRE_DEPLOY_REQUIRED`; a validacao local
tem head unico, mas nenhum upgrade Runtime foi executado nesta decisao.

### Checklist pre-deploy 0012

- [ ] CI green
- [ ] Runtime revision confirmada
- [ ] backup recente
- [ ] hash do backup verificado
- [ ] autorizacao de manutencao/deploy
- [ ] `alembic upgrade` forward-only controlado
- [ ] schema privacy validado
- [ ] health check
- [ ] smoke test
- [ ] AuditEvent verificado quando aplicavel
- [ ] aplicacao operacional

## Limitacoes e gates

| Gate | Estado | Efeito |
| --- | --- | --- |
| CI secret scanner | READY | scanner fail-closed cobre tracked e untracked nao ignorados; canario temporario foi detectado e release scan passou. |
| Dependency audit local | ACTION_REQUIRED, non-blocking | 7 advisories em `pip` 25.2 do virtualenv local; `pip` e tooling, nao dependencia runtime. Atualizar o tooling para 25.3/26.x. |
| Corpus real autorizado | PENDING_HUMAN_AUTHORIZATION | bloqueia dados reais. |
| Accountant signoff | PENDING | bloqueia dados reais. |
| Legal approval | PENDING | bloqueia dados reais. |
| CORS/HSTS/rate limit/metricas/alertas/IdP session revocation | PENDING | bloqueia exposicao externa. |

Nenhum segredo foi identificado. A fixture de redacao agora constroi o valor
sintetico em runtime; o scanner nao recebeu allowlist. O canario temporario
confirmou deteccao e o conjunto completo do release candidate passou sem
findings.
