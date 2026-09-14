# Configuração OIDC do aplicativo web

O Serdial21 usa arquitetura independente de fornecedor. Nenhum IdP está configurado no repositório. O cliente público usa Authorization Code + PKCE S256 e não possui client secret.

## Configuração pública obrigatória

| Campo em `app/config.js` | Uso |
| --- | --- |
| `authMode` | `oidc` ou `synthetic`; nunca inferido por falha |
| `oidc.issuer` | issuer exato esperado também pela API |
| `oidc.discoveryUrl` | metadata OIDC; pode ficar vazio para usar a rota padrão do issuer |
| `oidc.clientId` | identificador público do cliente browser |
| `oidc.redirectUri` | callback same-origin registrado no IdP |
| `oidc.postLogoutRedirectUri` | retorno same-origin após logout, quando suportado |
| `oidc.scope` | escopos mínimos; inclui `openid` |
| `oidc.audience` | audience quando exigida pelo fornecedor |
| `oidc.remoteLogoutEnabled` | opt-in somente após homologar `end_session_endpoint` |

Valores reais devem ser injetados pelo processo de ambiente, sem editar segredos no código. `client_secret`, private key, admin token, senha e refresh token são proibidos no navegador.

## Gates de ambiente

- produção exige HTTPS para issuer, discovery e endpoints descobertos;
- somente development aceita HTTP em `localhost` ou `127.0.0.1`;
- redirect e post-logout redirect precisam ter a mesma origem do aplicativo;
- CSP `connect-src` deve liberar apenas API, discovery e token endpoint homologados;
- callbacks devem ser registrados exatamente no IdP;
- CORS da API deve permitir somente origens aprovadas;
- a API e o cliente devem usar issuer e audience compatíveis;
- um teste com o IdP real deve confirmar login, expiração, logout e MFA antes de exposição.

TOKEN_RENEWAL=REAUTH_REQUIRED. REMOTE_IDP_LOGOUT=CONFIG_PENDING. IDP_GLOBAL_REVOCATION=PENDING.
