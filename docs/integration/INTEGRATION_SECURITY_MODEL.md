# Integration Security Model

## Recomendação M2M

`M2M_AUTH_RECOMMENDATION: READY_DESIGN`.

### MVP

- TLS obrigatório e validação normal de certificado;
- credencial distinta por sistema, direção e ambiente: `key_id` público + segredo de alta entropia em secret store/backend;
- HMAC-SHA-256 sobre método, path canônico, timestamp, request ID e hash dos bytes do body;
- headers `X-Serdial21-Key-Id`, `X-Serdial21-Timestamp`, `X-Serdial21-Signature`, `X-Request-Id` e `Idempotency-Key`;
- janela de timestamp curta (recomendação inicial: ±5 minutos), nonce/request ID armazenado até expirar e rejeição de replay;
- escopos mínimos por contrato/direção, rate limit por credencial e IP allowlist quando endereços forem estáveis;
- rotação sobreposta (chave ativa + próxima), revogação imediata e trilha de quem/onde/quando;
- nenhum segredo em frontend, payload, log, repositório ou dossiê.

API key sem assinatura não oferece integridade/replay suficiente e não é a opção recomendada isoladamente. `admin_auth_token`, `auth_token`, sessão localStorage e senha de usuário são proibidos em M2M.

### Hardening

Adotar OAuth2 Client Credentials com audience/scopes e tokens curtos quando houver IdP/operador compatível. Adicionar mTLS onde a emissão, rotação e revogação de certificados puderem ser operadas com confiabilidade. HMAC pode permanecer para assinatura de webhooks mesmo com OAuth2.

## Fronteira de autorização

Autenticação do Hub não concede autorização contábil nem `CompanyAccess` de usuário. O principal de serviço tem permissões explícitas para um conjunto de contratos e tenant(s) integrados. O B resolve a correlação externa para tenant/company permitido e falha fechado; IDs do payload não autorizam. Aprovação, rejeição e desbloqueio continuam exigindo contexto humano válido e as guardas do B.

O n8n não guarda permissões empresariais paralelas. A autorização final pertence ao sistema consumidor. Mensagens de negação não revelam recursos de outro tenant.

## Assinatura e canonicalização

Conceito de base assinada:

```text
METHOD + newline + /api/integrations/v1/... + newline
+ timestamp-UTC + newline + request-id + newline
sha256(raw-body)
```

Comparação de assinatura é constante; body é validado nos bytes recebidos. Algoritmo/versão e encoding entram no contrato congelado. Timestamp fora da janela, request ID já visto, key revogada ou assinatura inválida retornam erro estável e não sofrem retry automático.

## Dados e documentos

- minimizar payloads; não enviar XML/OFX, lançamentos completos, contatos desnecessários ou motivo livre quando código seguro bastar;
- short-lived URL escopada a um único objeto, uma operação e poucos minutos; sem credencial Drive;
- download somente pelo backend B, com limite de tamanho, timeout, media sniffing, hash, quarentena/malware policy e SSRF allowlist;
- B persiste evidência imutável controlada e registra origem/ref/hash; A mantém ownership operacional;
- logs contêm IDs, códigos, latência e hashes técnicos necessários, nunca segredo ou documento bruto;
- auditoria de negócio é persistida pelo sistema que aplica o efeito; log do Hub não a substitui.

## Operação e incidentes

Métricas mínimas: taxa/latência por contrato/versão/status, retries, DLQ, rejeições de assinatura/replay, idade da mensagem e reconciliação. Correlation/request/event IDs atravessam as camadas. Alertas evitam payload sensível.

Em comprometimento: revogar key/cert/token, bloquear escopo/IP, pausar consumidor afetado, preservar evidências, reconciliar desde o último checkpoint, rotacionar, avaliar exposição e seguir processos de incidente/LGPD. Replay deliberado nunca é resolvido com retry.

## Privacidade e retenção

Cada sistema preserva sua política, legal hold e autoridade. `CLIENT_DISABLED` e pedido de titular não disparam exclusão cruzada automática. `CROSS_SYSTEM_PRIVACY_WORKFLOW: FUTURE_DESIGN_REQUIRED` antes de real data, incluindo base/finalidade, retenção de cópias, DSR, backups e owner humano.

## Gates

Antes de homologação: threat model, contratos congelados, secret store, rotação/revogação ensaiadas, autorização negativa cross-tenant, replay/idempotência e logs minimizados. Antes de produção: infraestrutura TLS/rate limit/alertas, revisão CORS/guards do portal, audit trail A verificada, privacy/legal gates e E2E sintético aprovados.
