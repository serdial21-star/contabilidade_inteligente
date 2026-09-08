# Deploy, abort e rollback operacional

## Pre-deploy

O Incident Commander e o Technical Lead confirmam, sem expor valores de segredo:

1. CI verde para a revisao candidata; `alembic heads` possui apenas um head.
2. Runtime e banco corretos, banco alcancavel e backup recente com hash e destino confirmado conforme `BACKUP_RESTORE_RUNBOOK.md`.
3. Configuracao tipada, referencias de secrets e conectividade externa exigida estao presentes fora do Git.
4. Status dos incidentes, AccountLocks criticos e gates humanos foi revisado.
5. Janela, responsaveis, versao anterior da aplicacao e plano de abort estao identificados.

## Gate obrigatorio: migration 0012

`20260908_0012_privacy_controls` e `PRE_DEPLOY_REQUIRED`. Antes do proximo deploy Runtime: confirmar a revision atual, validar backup recente, revisar o upgrade forward-only, executar o upgrade em janela controlada, verificar tabelas/PK/FK/constraints/indices, confirmar `alembic current` e executar health e smoke. Esta execucao nao aplica a migration no Runtime.

## Deploy, health e smoke

1. Liberar somente a versao candidata na janela aprovada.
2. Verificar `/health/live` e `/health/ready` sem dados de cliente.
3. Executar login autenticado de prova e uma consulta read-only autorizada.
4. Confirmar correlation/request id nos logs sanitizados e `AuditEvent` quando a operacao de prova o produzir.
5. Registrar GO somente com os checks concluidos.

## Abort e rollback

Acionar `ABORT_DEPLOYMENT` por health ou banco falho, falha de auth boundary, migration/schema inesperado, falha de auditoria, sintoma cross-tenant ou taxa 5xx critica. Parar novo trafego, preservar evidencia e restaurar a versao anterior da aplicacao. Avaliar explicitamente a compatibilidade do banco antes de reabrir trafego.

Banco e migrations sao forward-only: rollback nao depende de `alembic downgrade`. Se houver incompatibilidade material, manter trafego parado e usar restore validado ou correcao forward aprovada, conforme o runbook de backup. Nao ha rollback automatico de banco.
