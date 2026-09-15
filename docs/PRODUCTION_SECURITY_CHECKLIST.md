# Checklist de segurança para homologação e produção

`READY` significa implementado no produto; não significa ambiente homologado. `CONFIG_REQUIRED`, `INFRA_REQUIRED` e `BLOCKER` impedem exposição até evidência.

| Área | Gate | Estado |
|---|---|---|
| APPLICATION | debug/reload desativados; erros genéricos; docs API explicitamente decididas | READY |
| APPLICATION | origins, hosts, URL pública, limites e headers validados no startup | READY |
| IDENTITY | issuer/audience/JWKS HTTPS e PKCE configurados para o ambiente | CONFIG_REQUIRED |
| IDENTITY | MFA, sessão curta, logout remoto e procedimento de revogação homologados | CONFIG_REQUIRED |
| NETWORK | certificado, TLS, redirect HTTPS e porta ASGI privada | INFRA_REQUIRED |
| NETWORK | HSTS validado sem preload | INFRA_REQUIRED |
| NETWORK | rate limit distribuído compartilhado e monitorado | INFRA_REQUIRED |
| DATABASE | credencial mínima, TLS/rede privada, backup criptografado e restore ensaiado | INFRA_REQUIRED |
| DATABASE | migration 0012 ensaiada/aplicada em janela aprovada | BLOCKER |
| SECRETS | provedor, ACL, rotação e separação por ambiente | INFRA_REQUIRED |
| SECRETS | scan sem segredo real no release | READY |
| UPLOAD | limites NF-e/OFX e parsers estruturais | READY |
| UPLOAD | malware scanning para upload binário genérico futuro | INFRA_REQUIRED |
| LOGGING | body/query/auth/claims ausentes; acesso e retenção definidos | READY |
| DEPENDENCIES | audit do release e política de correção | READY |
| DEPENDENCIES | lock/hashes reproduzíveis para build de produção | CONFIG_REQUIRED |
| DEPLOYMENT | observabilidade, alertas, backup e recuperação Phase 12 | BLOCKER |
| DEPLOYMENT | privacidade/legal Phase 13 e UAT Phase 14 | BLOCKER |
| DEPLOYMENT | real data e exposição externa formalmente aprovados | BLOCKER |

Resultado atual: aplicação pronta para configurar infraestrutura de homologação, mas `APPLICATION EXTERNAL EXPOSURE = NO_GO`.
