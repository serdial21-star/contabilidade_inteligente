# Runbook operacional mestre

## Escopo e seguranca

Este indice coordena a operacao controlada do piloto e aponta para os procedimentos especializados. Nunca incluir segredos, dumps, tokens, XML, OFX ou dados pessoais em tickets. Preservar `correlation_id`, referencias tecnicas de `AuditEvent` e logs sanitizados.

## Papeis e escalonamento

| Papel | Responsabilidade |
| --- | --- |
| Incident Commander | Classifica severidade, coordena decisao e linha do tempo. |
| Technical Lead | Diagnostica aplicacao, auth, logs e recuperacao tecnica. |
| Database Operator | Executa backup/restore autorizado e valida destino. |
| Security/Privacy Responsible | Contencao de acesso, evidencia e escalonamento de privacidade. |
| Accounting Reviewer | Avalia impacto em proposta, revisao e aprovacao contabil. |
| Communications Responsible | Comunica externamente somente apos decisao humana autorizada. |

Uma pessoa pode acumular papeis no piloto, mas, quando houver alternativa, nao deve aprovar sozinha recuperacao destrutiva, liberacao de legal hold ou comunicacao externa.

| Severidade | Exemplos | Acao inicial |
| --- | --- | --- |
| SEV1 | disclosure cross-tenant, credencial ampla, corrupcao de banco, indisponibilidade maior | conter, preservar evidencia e escalar imediatamente. |
| SEV2 | falha material de tenant, job critico ou backup | conter impacto, abrir incidente e definir recuperacao. |
| SEV3 | defeito isolado sem impacto de dados | registrar, priorizar e acompanhar. |

## Indice de procedimentos

| Situacao | Fonte canonica |
| --- | --- |
| Deploy, health, abort e rollback | `DEPLOY_RUNBOOK.md` |
| Backup e restore MariaDB | `BACKUP_RESTORE_RUNBOOK.md` |
| Onboarding, offboarding e acesso comprometido | `USER_LIFECYCLE_RUNBOOK.md` e `RUNBOOK_ONBOARDING_OFFBOARDING.md` |
| Rotacao de segredos | `SECRET_ROTATION_RUNBOOK.md` |
| Incidente de privacidade | `PRIVACY_INCIDENT_PROCESS.md` |
| AccountLock | `ACCOUNT_LOCK_PERSISTENCE.md` |
| Logs, correlacao e metricas locais | `OBSERVABILITY_MVP.md` |
| Inicio diario e GO/NO-GO | `PILOT_OPERATIONAL_CHECKLIST.md` |

## Resposta comum a incidente

1. Registrar horario UTC, operador, servico e correlation/request id; atribuir severidade provisoria.
2. Conter sem destruir evidencia: retirar trafego, desabilitar acesso pelo IdP, pausar job ou restringir integracao.
3. Confirmar tenant e company afetados apenas por consultas autorizadas.
4. Preservar `AuditEvent`, logs sanitizados, hashes e configuracao relevante em acesso restrito.
5. Recuperar somente pelo procedimento aplicavel; migrations sao forward-only.
6. Registrar decisao, impacto conhecido, recuperacao e acoes corretivas.

## Gates atuais

- `MIGRATION_0012 = PRE_DEPLOY_REQUIRED`: `20260908_0012_privacy_controls` exige upgrade forward-only controlado antes do proximo deploy Runtime.
- Dados reais exigem corpus autorizado, assinatura do contador e aprovacao juridica; sao gates humanos.
- CORS allowlist, HSTS no proxy, rate limit distribuido, metricas centrais e transporte de alertas sao `PENDING_BEFORE_EXTERNAL_EXPOSURE`.
- `POST_UNLOCK_WORKFLOW = OUT_OF_SCOPE`: liberar AccountLock nao retoma trabalho automaticamente.
