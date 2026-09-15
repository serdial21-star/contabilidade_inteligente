# Infraestrutura de segurança — Phase 11

## Fronteiras e confiança

O navegador recebe somente o frontend estático, delega autenticação ao IdP por Authorization Code + PKCE e mantém o access token em memória. `sessionStorage` contém apenas a transação PKCE efêmera; `localStorage` contém somente preferências de layout. A API aceita Bearer JWT RS256, valida assinatura, algoritmo, issuer, audience e tempo, resolve a identidade interna e revalida tenant, membership, CompanyAccess, papel e permissão no efeito.

O fluxo externo previsto é `browser -> HTTPS reverse proxy/plataforma -> ASGI`. Somente o proxy autorizado pode definir informações de cliente encaminhadas; o aplicativo não confia em `X-Forwarded-For` para rate limit. Banco e object storage ficam em rede privada, usam identidades distintas e nunca são acessados pelo browser. Segredos pertencem ao ambiente/provedor de segredos, não ao frontend, código, logs ou auditoria.

Documento, XML, OFX, nomes de arquivo, campos de busca, headers e texto de evento são dados não confiáveis. Limites de corpo atuam antes do parsing; parsers estruturais mantêm seus próprios limites; rotas tipadas limitam strings, listas e paginação. Malware scanning continua `INFRASTRUCTURE_GAP` e não é substituído por validação estrutural.

## Controles em runtime

| Controle | Estado | Evidência/limite |
|---|---|---|
| JWT/OIDC | READY | RS256 fixo, JWKS cacheado, issuer/audience/exp/iat/sub/tenant obrigatórios |
| Tenant/empresa | READY | contexto autenticado + consultas tenant/company-aware + CompanyAccess |
| CORS | READY | allowlist exata; sem credenciais por cookie; origem desconhecida não recebe ACAO |
| Host | READY | `TrustedHostMiddleware`; allowlist obrigatória fora de local/test |
| Headers/cache | READY | CSP da API, frame denial, nosniff, referrer/permissions policy e `no-store` |
| HSTS | READY_FOR_DEPLOYMENT | emitido em production; exige `EXTERNAL_HTTPS=true`; preload adiado |
| Corpo/upload | READY | geral, NF-e e OFX possuem limites independentes e dupla validação |
| Rate limit | READY | backend em memória para local/test; porta injetável distribuída e fail-closed fora deles |
| Erros/logs | READY | erro 500 genérico fora de local/test; logs sem body/query/header/claims |
| Request ID | READY | UUID validado ou substituído; propagado na resposta e logs técnicos |

## Produção e autoridade

Homologação e produção não iniciam com debug, HTTP externo, OIDC incompleto, origem/host ausente, banco ausente ou rate limit em memória. O adaptador distribuído é dependência de composição e infraestrutura, não um fallback opcional. Produção desabilita Swagger/ReDoc/OpenAPI por padrão; isso reduz superfície, mas não substitui autorização.

JWKS falho, chave desconhecida ou rotação não resolvida negam autenticação. `PyJWKClient` mantém cache limitado por cinco minutos e busca novamente conforme seleção de `kid`; nenhuma falha aceita token não verificado. Revogação global continua `PROVIDER_DEPENDENT`: mitigação exige tokens curtos, revogação de sessão no IdP, rotação de chaves e revalidação interna por request.

Não há cookie de autenticação na API, portanto CSRF é `NOT_APPLICABLE_CURRENT_BEARER_MODEL`. Se cookies autenticados forem introduzidos, a decisão deve ser revista antes da exposição.

## Gaps externos preservados

- certificado/TLS, redirect HTTP→HTTPS e proxy confiável: `INFRA_REQUIRED`;
- adaptador/serviço distribuído de rate limit: `CONFIG_REQUIRED`;
- IdP real, MFA, logout remoto e revogação: `PENDING`/provider-dependent;
- lockfile/hash de dependências: `DEPENDENCY_PINNING_GAP`;
- backup/restore e observabilidade central: Phase 12;
- HSTS preload: `DEFERRED`;
- exposição externa e dados reais: `NO_GO`.

## Auditoria de dependências

Em 15/09/2026, `pip check` não encontrou dependências quebradas. `pip-audit --local` não encontrou vulnerabilidade em dependência de runtime do Serdial21; reportou 12 registros conhecidos exclusivamente no `pip 25.2`, ferramenta do ambiente de build/desenvolvimento, com correções disponíveis em versões posteriores. Classificação: `ACCEPTED_NON_RUNTIME_FINDINGS`, runtime blockers `0`. O ambiente de build deve atualizar o instalador antes de produzir um release; nenhuma dependência foi alterada automaticamente nesta fase. O pacote local `serdial21` não existir no PyPI é esperado.
