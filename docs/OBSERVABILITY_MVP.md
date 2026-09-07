# Observabilidade técnica do MVP

Esta camada não substitui nem escreve `AuditEvent`. Auditoria continua sendo o
registro de negócio append-oriented; observabilidade serve para diagnóstico e
operação do piloto.

## Canais separados

| Canal | Logger | Conteúdo permitido |
| --- | --- | --- |
| Log técnico | `serdial21.technical` | evento HTTP, método, caminho sem query, status, duração e tipo sanitizado de erro |
| Evento de segurança | `serdial21.security` | negações de autorização e motivo técnico sem IDs de usuário, tenant ou empresa |
| Evento de acesso a dados | `serdial21.data_access` | leitura de evidência permitida, negada ou com falha de integridade, sem identificador ou conteúdo |
| Auditoria de negócio | Persistência `AuditEvent` | permanece fora desta camada e preserva suas próprias regras de integridade |

Os logs são JSON e carregam `correlation_id` quando houver contexto HTTP. O
sanitizador remove campos de senha, token, segredo, XML, prompt e dados
bancários. Mensagens de exceção não são registradas; somente o nome sanitizado
da classe de erro é emitido.

## Métricas mínimas

`MetricsRegistry` mantém agregados locais sem labels de tenant, empresa, conta,
documento ou usuário:

- `imports_total`, `errors_total`, `proposals_total`;
- `approvals_total`, `rejections_total`, `pending_total`;
- `exports_total`, `retries_total`, `reconciliations_total`;
- `processing_duration_count` e `processing_duration_seconds`.

O request middleware registra duração e erro HTTP. A jornada NF-e para Domínio
incrementa importação, proposta, aprovação/rejeição, pendência, exportação e
retry, além de medir o processamento da preparação. A métrica de conciliação
está disponível no registry para a futura borda de aplicação: a conciliação
atual ainda é domínio puro, sem caso de uso/persistência a instrumentar.

## Limites de operação

O registry é propositalmente local ao processo e não expõe endpoint HTTP nesta
fatia. Para múltiplas réplicas, retenção, alertas e scraping, a infraestrutura
do piloto deve fornecer coletor/exportador aprovado. Não foi criado endpoint de
métricas sem autenticação.
