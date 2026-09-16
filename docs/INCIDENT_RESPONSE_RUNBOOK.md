# Runbook de resposta a incidentes

## Ciclo e papéis

Estados: `DETECTED -> TRIAGED -> CONTAINED -> RECOVERING -> RESOLVED ->
POSTMORTEM`. O Incident Commander coordena e autoriza mudanças; Technical Lead
diagnostica/recupera; Security/Privacy trata identidade e obrigação legal;
responsável contábil decide impacto de negócio. Registre decisões e horários
sem copiar payload sensível.

## Resposta comum

1. Classifique impacto, ambiente, início e sinais; abra identificador do
   incidente.
2. Preserve logs, métricas, AuditEvents, hashes e artefatos. Não destrua
   evidência.
3. Contenha o menor escopo possível; em dúvida de integridade, pare mutações
   afetadas.
4. Determine tenants/empresas potencialmente afetados por consulta autorizada,
   nunca por exposição em métrica ou canal geral.
5. Recupere por release, configuração, serviço ou restore conforme a causa.
6. Valide boundaries, integridade, readiness e smoke antes de reabrir.
7. Comunique pelos responsáveis aprovados; notificações legais pertencem à
   Phase 13.
8. Faça postmortem sem culpabilização, com causa, impacto, timeline e ações.

## Cenários

- Segurança: isolar aplicação quando necessário, revogar/rotacionar credenciais,
  encerrar sessões via IdP, ajustar rate limit, preservar logs/auditoria e
  acionar privacidade. Nunca apagar evidência do atacante.
- Integridade contábil: parar mutações do escopo, preservar estado e auditoria,
  identificar tenant/company, comparar versões/hashes e corrigir por workflow,
  evento compensatório ou recuperação aprovada — nunca SQL manual sem rastro.
- Banco/aplicação: diferenciar processo vivo de readiness, conter tráfego e usar
  o [runbook de recuperação](RECOVERY_RUNBOOK.md).
- Backlog/processamento: observar taxa de falha, idade/volume de itens atuais e
  rejeições repetidas; não inventar fila. Pausar a origem afetada, preservar
  idempotência e reconciliar antes de retry.
- Release ruim: abortar, avaliar compatibilidade de schema e restaurar somente
  a aplicação quando o banco estiver íntegro.
- Backup falho: preservar último válido, registrar risco ao RPO, corrigir causa,
  repetir e confirmar checksum; ausência além de 24 h é CRITICAL.

Falha de AuditEvent em caminho decisório é condição crítica porque efeito e
auditoria devem ser atômicos. Falha de agregador de logs/métricas/alertas é
best-effort e deve ser reparada, mas não autoriza ignorar falha de auditoria.
