# Provedor OIDC de desenvolvimento

Não é um IdP real e nunca deve ser usado fora de `development`/`test`
(`scripts/dev_identity_provider.py` recusa rodar em `homologation`/`production`).
Serve só para gerar tokens RS256 válidos e testar a API real do Sistema B
localmente, sem escolher ainda o provedor de identidade definitivo (essa
decisão é maior e continua em aberto — ver `docs/OIDC_CONFIGURATION.md`).

## Configuração (uma vez)

No `.env` (raiz do projeto, nunca versionado):

```
OIDC_ISSUER=http://127.0.0.1:8090
OIDC_AUDIENCE=serdial21-dev-api
OIDC_JWKS_URL=http://127.0.0.1:8090/.well-known/jwks.json
```

## Uso

```powershell
# 1) gerar a chave uma única vez (evita duas chaves por corrida entre processos)
.\.venv\Scripts\python.exe scripts\dev_identity_provider.py init-key

# 2) num terminal, subir o endpoint JWKS (deixar rodando)
.\.venv\Scripts\python.exe scripts\dev_identity_provider.py serve

# 3) noutro terminal, emitir um token para testar
.\.venv\Scripts\python.exe scripts\dev_identity_provider.py issue-token --subject dev-sergio --tenant-id <TENANT_ID>
```

O token expira em 60 minutos por padrão (`--minutes`). O `sub` (`--subject`)
precisa bater exatamente com `users.provider_subject` do usuário que for
criado no Sistema B (próximo passo, ver dossiê da sessão).

## O que valida (testado em 2026-09-24)

O `verify()` chamado é o mesmo código que a API usa de verdade
(`serdial21.modules.identity.adapters.inbound.oidc.OidcJwtVerifier`, via
`bootstrap.identity.build_oidc_verifier`): busca a chave pública no JWKS por
HTTP, confere assinatura RS256, `iss`, `aud`, `exp`, `iat`, `sub` e
`tenant_id`. Testes automatizados: `tests/unit/test_dev_identity_provider.py`
(ambiente recusado fora de dev/test, chave estável entre chamadas, token só
verifica com a chave certa).

## Limites (de propósito)

- Chave fica em `local_data/dev_oidc/private_key.pem` (git-ignorado).
- Sem revogação, sem refresh, sem `/.well-known/openid-configuration` (a API
  não usa descoberta, só a `OIDC_JWKS_URL` direta).
- Não decide nem substitui o provedor de produção da Fase 11.
