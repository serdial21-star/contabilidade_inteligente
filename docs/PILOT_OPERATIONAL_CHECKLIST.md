# Checklist operacional do piloto

## Inicio diario ou janela de deploy

- [ ] CI da revisao candidata esta verde e Alembic possui head unico.
- [ ] `/health/live`, `/health/ready`, conectividade de banco e IdP/JWKS estao saudaveis.
- [ ] Backup recente, hash e destino de restore foram confirmados; nenhum backup conhecido foi sobrescrito por falha.
- [ ] Revision Runtime e gate da migration 0012 foram avaliados para a janela.
- [ ] Incidentes abertos, negacoes de auth relevantes e AccountLocks criticos foram revisados por correlation id e logs sanitizados.
- [ ] Nao existe bloqueio tecnico conhecido para o escopo sintetico interno.

## GO/NO-GO para futura decisao humana

| Categoria | Estado atual | Gate remanescente |
| --- | --- | --- |
| Technical, security, recovery e operations | READY para piloto sintetico interno | executar somente a janela controlada e seguir os runbooks. |
| Accounting | READY tecnico sintetico | `ACCOUNTANT_SIGNOFF = PENDING`. |
| Privacy/legal e dados reais | BLOCKED | corpus real autorizado e aprovacao juridica pendentes. |
| External exposure | BLOCKED | CORS allowlist, HSTS/proxy, rate limit distribuido, metricas centrais e alert transport. |
| External integration (Dominio) | BLOCKED_FOR_HOMOLOGATION | layout, golden files e homologacao. |

Esta lista nao concede automaticamente autorizacao para iniciar piloto ou usar dados reais.
