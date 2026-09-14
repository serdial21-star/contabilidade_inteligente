# Integração de autenticação do frontend

Inventário consolidado da Phase 04B. A interface apresenta capacidades; autenticação, tenant, CompanyAccess e autorização continuam server-authoritative.

## Contratos efetivos

| Item | Estado | Contrato |
| --- | --- | --- |
| Provedor IdP | NOT_CONFIGURED | Nenhum fornecedor ou URL real foi escolhido. |
| API authentication | IMPLEMENTED | JWT RS256 OAuth 2.0/OIDC em `Authorization: Bearer`; valida `iss`, `aud`, `exp`, `iat`, `sub` e `tenant_id`. |
| Browser authentication | READY_IMPLEMENTATION | Authorization Code + PKCE S256, discovery, state aleatório, transação expirada em 10 minutos e callback higienizado. |
| Login endpoint | NOT_APPLICABLE | Usuário, senha, MFA e recuperação pertencem ao IdP. |
| Current application | READY | `GET /api/v1/identity/me`, sem parâmetros de escopo. |
| Context validation | READY | `GET /api/v1/identity/context?company_id=<UUID>` permanece para revalidação pontual de `company.read`. |
| Token policy | READY | Access token somente no closure da sessão em memória; refresh token não é solicitado nem persistido. |
| Logout | PARTIAL_EXTERNAL | Estado local é limpo; RP-initiated logout depende de metadata/configuração e revogação global continua externa. |

## Projeção autenticada

`GET /api/v1/identity/me` deriva tudo do `AuthenticatedPrincipal` produzido após validação do Bearer. Não aceita `tenant_id`, `user_id`, papel, empresa ou permissão do cliente.

```json
{
  "user": {"id": "<uuid>", "display_name": "<nome>"},
  "tenant": {"id": "<uuid>", "display_name": "<escritório>"},
  "companies": [
    {"id": "<uuid>", "display_name": "<empresa>", "permissions": ["company.read"]}
  ],
  "permissions": ["identity.manage"]
}
```

`permissions` contém capacidades tenant-wide. Cada empresa contém a união resolvida de bindings tenant-wide e company-scoped. Os códigos são exatos, ordenados e sem curingas. Empresas são lidas somente por CompanyAccess ativo e vigente no tenant do token. Usuário inativo, tenant inativo, Membership ausente/ambíguo ou identidade não provisionada resultam em `403 access denied`.

Somente nome de exibição e IDs opacos necessários são expostos. Email, claims, token, dados fiscais, papéis internos e metadados de banco não fazem parte da resposta.

## Fluxo do navegador

```text
APP OPEN
-> AUTH_MODE explícito
-> OIDC CONFIG VALIDATION
-> DISCOVERY
-> AUTHORIZATION CODE + PKCE S256
-> STATE + AGE VALIDATION
-> CODE EXCHANGE
-> ACCESS TOKEN IN MEMORY
-> GET /identity/me
-> AUTHORIZED SHELL
```

O estado e o verifier PKCE ficam temporariamente em `sessionStorage` apenas para sobreviver ao redirect; são removidos antes da troca do código. Nenhum token usa Web Storage. Parâmetros de callback são removidos da URL antes da troca. Endpoints exigem HTTPS, com exceção explícita apenas para `localhost`/`127.0.0.1` em development, e redirects devem permanecer same-origin.

401 limpa sessão e retorna ao login. 403 não revela a causa interna. Falha de discovery, rede, metadata, issuer, state, PKCE ou troca de código falha fechada. Não existe fallback automático de OIDC para synthetic.

## Gaps remanescentes

| ID | Classificação | Gap | Gate |
| --- | --- | --- | --- |
| AF-01 | CONFIG_PENDING | fornecedor, issuer, discovery, client ID, callbacks e CSP allowlist reais | produção IdP |
| AF-02 | CONFIG_PENDING | endpoint de logout remoto verificado e habilitação explícita | IdP homologado |
| AF-03 | EXTERNAL_PENDING | revogação global da sessão/token | infraestrutura IdP |
| AF-04 | DEFERRED | perfil staging e origens/CORS correspondentes | environment phase |

OIDC_CLIENT_IMPLEMENTATION=RESOLVED; CURRENT_USER=RESOLVED; TENANT_CONTEXT=RESOLVED; AUTHORIZED_COMPANIES=RESOLVED; PERMISSION_PROJECTION=RESOLVED; TOKEN_RENEWAL=REAUTH_REQUIRED.
