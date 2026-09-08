# Identidade e segurança de tenant

Data da decisão: 08/09/2026

## Estratégia adotada

O Serdial21 aceita **access tokens OAuth 2.0/OIDC em formato JWT**, emitidos por
um provedor de identidade externo consolidado. O IdP é responsável por senha,
MFA, recuperação de conta, política de sessão e autenticação primária. A
aplicação não armazena nem valida senhas.

A integração é compatível com IdPs que publiquem JWKS e emitam JWT RS256. A
escolha comercial do IdP permanece operacional; não é necessário alterar o
domínio para trocar de fornecedor compatível.

O token é aceito somente após validação criptográfica de assinatura RS256,
`iss`, `aud`, `exp`, `iat`, `sub` e do claim privado `tenant_id`. Algoritmos não
configurados não são aceitos. Chaves públicas são obtidas por HTTPS no endpoint
JWKS e mantidas em cache por tempo limitado. Token, claims completos e dados
pessoais não são registrados em log.

## Cadeia de confiança

```text
IdP -> Bearer access token validado -> (issuer, subject)
    -> User interno -> Membership ativo no tenant do token
    -> CompanyAccess ativo para a empresa selecionada
    -> RoleBinding ativo -> Permission ativa -> operação
```

`tenant_id` no token seleciona o tenant, mas não concede acesso: a aplicação
sempre exige que o usuário interno tenha exatamente um membership ativo nesse
tenant. `company_id` recebido em URL, query ou body é apenas seletor e sempre é
revalidado contra empresa, tenant e CompanyAccess. Papel e permissão vêm
exclusivamente do banco interno.

A chave externa do usuário é o par imutável `(provider_issuer,
provider_subject)`. Email e nome de exibição são atributos, nunca identidade ou
autoridade.

## Configuração

As configurações vêm exclusivamente do ambiente:

- `OIDC_ISSUER`: issuer exato do access token;
- `OIDC_AUDIENCE`: audience exclusiva da API Serdial21;
- `OIDC_JWKS_URL`: endpoint HTTPS de chaves públicas;
- `OIDC_CLOCK_SKEW_SECONDS`: tolerância temporal, máximo de 120 segundos;
- `OIDC_JWKS_TIMEOUT_SECONDS`: timeout de busca de chave.

Produção falha ao iniciar sem a configuração OIDC completa e HTTPS. Segredos,
client secrets e tokens não pertencem ao `.env.example`, ao banco ou aos logs.
Esta validação não exige client secret porque a API valida access tokens
assimétricos com chaves públicas.

O IdP deve emitir `tenant_id` como UUID no access token destinado à audience da
API. Para usuário com acesso a mais de um tenant, a seleção deve ocorrer no
contexto de organização do IdP antes da emissão; cada token contém um único
tenant. Essa seleção continua subordinada ao membership interno.

## Autorização e respostas seguras

Os controles existentes de `AuthorizationService` não foram substituídos. A
autenticação apenas produz um principal interno e o serviço existente revalida,
em toda operação:

- usuário ativo;
- membership ativo e vigente;
- pertença da empresa ao tenant;
- CompanyAccess ativo e vigente;
- RoleBinding ativo e vigente;
- papel exigido, quando aplicável;
- permissão atômica ativa.

Token ausente, malformado, expirado, com assinatura, issuer ou audience
inválidos retorna `401 authentication failed`. Identidade não vinculada,
cross-tenant, cross-company, usuário ou vínculo revogado e permissão
insuficiente retornam o mesmo `403 access denied`. A resposta não revela se o
recurso, usuário, tenant ou empresa existe.

## Onboarding e offboarding

As mutações exigem a nova permissão tenant-wide `identity.manage`.

`POST /api/v1/identity/onboarding` cria ou reativa o usuário vinculado ao
issuer configurado, cria membership, CompanyAccess e RoleBinding somente para
empresas e papel ativos do tenant do operador. O efeito e `identity.onboarded`
são gravados na mesma transação.

`POST /api/v1/identity/users/{user_id}/offboard` revoga membership,
CompanyAccess e RoleBinding, desativa o usuário quando não há outro membership
ativo e grava `identity.offboarded` na mesma transação. Auditoria histórica não
é removida. Auto-offboarding pelo endpoint é negado para evitar perda acidental
do último administrador.

Tokens já emitidos não recuperam acesso após revogação: todos os vínculos
internos são consultados novamente a cada operação. Revogação imediata da
sessão no próprio IdP continua responsabilidade operacional do administrador.

## Migration e compatibilidade

A revision `20260908_0010` adiciona `users.provider_issuer`, substitui a
unicidade global de `provider_subject` pela unicidade composta
`(provider_issuer, provider_subject)` e cadastra `identity.manage`. Registros
anteriores recebem temporariamente `urn:serdial21:legacy`; isso evita vinculá-los
silenciosamente a um IdP real.

A migration não concede `identity.manage` a papel algum e não converte sujeitos
legados automaticamente. A vinculação do primeiro administrador é uma operação
controlada descrita no runbook. Esse comportamento fail-closed evita elevação de
privilégio durante o upgrade.

## Evidência automatizada

Os testes cobrem assinatura RSA real, expiração, resposta uniforme, onboarding,
offboarding, AuditEvent, cross-tenant, cross-company, empresa desconhecida,
usuário desativado, membership revogado, RoleBinding revogado e ausência de
CompanyAccess. A suíte de autorização preexistente continua ativa e a migration
é exercitada em `base -> head -> base` no SQLite, sem remover essa camada rápida.

## Limites operacionais restantes

- provisionar e homologar um IdP real com MFA e claim `tenant_id`;
- vincular o primeiro administrador pelo procedimento de bootstrap controlado;
- aplicar a revision 0010 no MariaDB somente após backup e ensaio no Lab;
- definir tempos de sessão, revogação no IdP e monitoramento de falhas JWKS;
- realizar UAT com as alçadas reais do escritório.

