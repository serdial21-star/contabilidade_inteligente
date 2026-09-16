# Arquitetura de observabilidade

## Objetivo e estado

A Phase 12 fornece sinais locais, contratos de exportação e procedimentos para o
piloto sintético. Ela não provisiona agregador, backend de métricas ou painel e
não autoriza exposição externa. Observabilidade técnica nunca substitui o
`AuditEvent` append-oriented e atômico das decisões de negócio.

| Capacidade | Estado anterior | Evidência | Lacuna tratada na Phase 12 |
|---|---|---|---|
| Logs JSON | parcial | `shared_kernel/observability.py` | serviço, ambiente, request/correlation IDs e redaction de valores |
| Request/correlation ID | parcial | middleware de correlação | IDs separados, UUID validado e contexto isolado |
| Métricas | local/sem labels | `MetricsRegistry` | esquema fechado, labels baixas e formato Prometheus |
| Health | live/ready | rotas `/health` | respostas mínimas e alerta deduplicado de DB |
| Alertas | ausente | `shared_kernel/alerting.py` | porta neutra, sink nulo/fake e cooldown |
| Backup/restore | runbook e evidência histórica | documentos de 08/09/2026 | tooling testável e drill local sintético |

## Modelo de sinais

| Sinal | Finalidade | Autoridade | Sensibilidade |
|---|---|---|---|
| Log | execução, erro e diagnóstico técnico | não é evidência contábil | minimizado e sanitizado |
| Métrica | tendência agregada, taxa e latência | não explica caso individual | sem IDs de cliente |
| Liveness | processo responde | orquestração | somente `status` |
| Readiness | dependência crítica permite tráfego | orquestração | somente `ready/not_ready` |
| AuditEvent | decisão/efeito de negócio e sua linhagem | autoritativo no Serdial21 | acesso empresarial controlado |
| Alerta | mudança operacional que demanda ação | sinal best-effort | categoria/severidade/runbook |

## Logging estruturado e contexto

Cada linha técnica é JSON com nomes estáveis: `timestamp`, `level`, `service`,
`environment`, `event_name`, `request_id`, `correlation_id` e `fields`.
Eventos HTTP usam `method`, template da `route`, `status_code` e `duration_ms`.
O caminho bruto e a query não são registrados.

`request_id` identifica uma requisição. `correlation_id` conecta uma jornada
com múltiplos passos e pode coincidir com o request ID quando o chamador não
fornece correlação. Somente UUID válido é aceito nos headers. `contextvars`
impede vazamento entre requisições; a correlação persistente de negócio
continua sendo a já existente no `AuditEvent`, sem coluna nova.

É proibido registrar Authorization/Bearer, tokens OIDC, senhas, chaves,
credenciais/URL completa de banco, cookies, XML/OFX brutos, conta bancária,
descrição financeira integral, evidência contábil ou dado pessoal
desnecessário. Chaves sensíveis são removidas, valores com marcadores de
segredo/XML/OFX são redigidos, strings são limitadas e exceções registram
somente o tipo. Stack trace interno só é permitido em acesso operacional
restrito; nunca é resposta ao cliente.

Política de nível: DEBUG apenas local; INFO para ciclo normal; WARNING para
condição anormal recuperável; ERROR para operação falha que exige atenção;
CRITICAL para indisponibilidade severa. Produção usa INFO por padrão.

## Métricas

O registry em memória possui schema fechado. Labels permitidas são somente
classes estáveis como método, template de rota, classe HTTP, origem
`nfe|ofx`, resultado, decisão e bucket. Tenant, empresa, usuário, conta,
documento, request/correlation ID e texto controlado pelo cliente são proibidos.

Instrumentos implementados incluem requests, duração HTTP, 5xx, autenticação,
autorização, rate limit, payload grande, rejeição de parser, importação NF-e,
proposta, decisão e AccountLock. Os contadores legados permanecem durante o
piloto por compatibilidade. O endpoint `/internal/metrics` é opt-in, responde
como inexistente sem Bearer operacional válido e também deve ser bloqueado no
proxy para a rede privada. Não é endpoint de internet nem de portal de cliente.

## Vida do processo, privacidade e falhas

Startup registra apenas ambiente, modo de segurança, ativação do endpoint e
tipo do backend de rate limit. Shutdown fecha o engine e registra término. A
liveness não consulta dependências; a readiness faz somente `SELECT 1` pelo
pool configurado. Timeout de conexão é limitado por
`DATABASE_CONNECT_TIMEOUT_SECONDS` (10 s por padrão).

Falha de log central, exportação de métrica ou transporte de alerta não deve
interromper transação contábil. Falha da persistência atômica de AuditEvent
continua sendo regra crítica e não recebe esse tratamento best-effort.

Retenção proposta, sujeita à Phase 13: logs de aplicação 30 dias, logs de
segurança 90 dias, métricas agregadas 90 dias e metadados de backup conforme a
retenção do backup. Auditoria segue política legal própria e não é apagada na
Phase 12. Acesso futuro a logs/métricas exige identidade operacional, mínimo
privilégio e separação de LOCAL/TEST/HOMOLOGATION/PRODUCTION.

OpenTelemetry e tracing distribuído ficam adiados: um monólito com JSON,
métricas e IDs de correlação cobre o piloto sem dependência pesada. Connect Hub
poderá justificar reavaliação futura.
