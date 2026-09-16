# Runbook de recuperação

## Autoridade e acionamento

Acione por perda/corrupção suspeita, banco indisponível prolongado, backup
vencido/inválido ou falha de migration. Incident Commander decide restore com
Technical Lead e responsável por dados; uma recuperação real exige aprovação
explícita. Suspenda tráfego/mutações afetadas, preserve logs e AuditEvents e
nunca apague evidência.

## Banco indisponível

1. Confirme liveness e readiness; não transforme outage temporário em loop de
   restart.
2. Restrinja tráfego novo e preserve requests em andamento conforme a borda.
3. Verifique rede/pool/serviço sem imprimir conexão ou credencial.
4. Se não houver perda de dados, recupere o serviço e valide readiness; não
   restaure banco por reflexo.
5. Se houver perda/integridade duvidosa, siga restore abaixo.

## Seleção e restore

1. Identifique release da aplicação, migration head, horário do incidente e RPO
   tolerável.
2. Escolha backup anterior ao incidente; confirme metadados, retenção e cadeia
   de custódia.
3. Recalcule SHA-256 antes de abrir o artefato.
4. Provisione destino novo, isolado e sem dados a preservar. Nunca restaure
   diretamente sobre banco ativo.
5. Confirme por consulta que o destino é exatamente o aprovado.
6. Restaure com credencial fora da linha de comando e capture apenas status,
   duração e erro sanitizado.
7. Valide migration head, tabelas críticas, schema/constraints/índices,
   contagens sintéticas/esperadas, AuditEvent legível, AccountLock e leitura ORM
   tenant-aware.
8. Alinhe código e schema compatíveis; execute smoke read-only, liveness e
   readiness.
9. O Incident Commander aprova cutover/reabertura. Monitore 5xx, latência,
   processamento e auditoria.
10. Registre tempos, decisões, desvios e postmortem.

Checksum divergente, validação estrutural falha ou destino incorreto interrompe
imediatamente o restore e gera alerta CRITICAL. Não se corrige histórico à mão.

## Deploy ruim versus migration ruim

Um deploy de aplicação com banco compatível pede abort, retorno ao artefato
anterior e smoke; não pede restore de banco. Se schema já mudou, valide
compatibilidade antes do rollback da aplicação.

Migration de produção é forward-only. Prefira migration corretiva revisada
quando dados íntegros permitirem; use backup/restore quando houver perda,
corrupção ou incompatibilidade incontornável. `alembic downgrade` casual não é
rollback operacional.

Para a migration `20260908_0012_privacy_controls`, ainda
`PRE_DEPLOY_REQUIRED`: (1) conferir versão atual; (2) criar backup; (3) verificar
artefato/hash; (4) opcionalmente restaurar em isolamento; (5) aplicar 0012 em
janela aprovada; (6) smoke; (7) readiness; (8) monitorar. Phase 12 não executa
essa sequência.

## Desastre

Reproduza código pelo release, banco por backup protegido, configuração pelo
provedor de secrets, IdP por configuração aprovada e monitoramento por IaC ou
runbook. Restore de object storage precisa reconciliar hashes e referências com
o banco. Multi-região não é requisito atual.
