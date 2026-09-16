# Política de alertas operacionais

## Modelo

Alertas representam condições acionáveis, não cada log. A porta `AlertSink` é
neutra; Phase 12 deixa o transporte real `READY_FOR_CONFIGURATION`, sem SMTP,
Slack, Teams, PagerDuty ou credencial. `AlertDispatcher` aplica cooldown por
chave e uma falha do sink gera evento sanitizado sem derrubar a aplicação.

Severidades:

- INFO: mudança conhecida, sem ação imediata;
- WARNING: degradação ou tendência que pede triagem em horário operacional;
- CRITICAL: indisponibilidade, risco de perda/integridade ou recuperação falha.

## Catálogo inicial

| Categoria | Sinal | Conceito de limiar | Severidade | Expectativa | Runbook |
|---|---|---|---|---|---|
| SERVICE | 5xx sustentado/latência degradada | janela e baseline do piloto, não evento isolado | WARNING/CRITICAL | triagem e contenção | `INCIDENT_RESPONSE_RUNBOOK.md` |
| DATABASE | readiness falha | uma transição para indisponível; cooldown evita tempestade | CRITICAL | impedir tráfego novo e diagnosticar | `RECOVERY_RUNBOOK.md#banco-indisponível` |
| SECURITY | 401/403/429 anormais | desvio sustentado do baseline por classe | WARNING | investigar origem sem usar strings do atacante | Phase 11 + incident runbook |
| PROCESSING | falhas NF-e/OFX ou backlog cresce | taxa/idade acima do baseline sintético | WARNING/CRITICAL | pausar lote afetado e preservar evidência | incident runbook |
| BACKUP | job falha, artefato vazio/hash ausente ou backup vencido | qualquer execução inválida ou ausência além do RPO alvo | CRITICAL | preservar último válido e repetir com autorização | `RECOVERY_RUNBOOK.md` |
| RECOVERY | checksum/restore/validação falha | qualquer etapa falha | CRITICAL | não liberar tráfego; escolher outro backup | `RECOVERY_RUNBOOK.md` |

Os números definitivos de janela/percentil dependem do baseline coletado no
piloto e não são SLA. Uma validação 4xx isolada não gera alerta. Labels nunca
incluem tenant, empresa, documento, pessoa ou texto enviado pelo cliente.

## Deduplicação, transporte e canário

O dispatcher reserva a janela de cooldown antes da entrega para impedir rajada
concorrente. Integração futura deve alertar em transições `healthy -> failing` e
`failing -> recovered`, preservar a mesma chave e oferecer canal secundário
para CRITICAL. Falha contínua do próprio canal precisa de heartbeat/canário
externo; observar o canal por ele mesmo não é suficiente.

O fake `InMemoryAlertSink` testa WARNING, CRITICAL, cooldown e falha. Não existe
endpoint público para disparar alerta. Em homologação, o operador deverá
executar canário identificado como teste e confirmar recebimento antes de
aprovar exposição.
