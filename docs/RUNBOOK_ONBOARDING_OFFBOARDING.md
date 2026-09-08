# Runbook de onboarding e offboarding

## Escopo e responsabilidades

Este procedimento administra acesso humano ao Serdial21. Ele não cria regra,
conta ou efeito contábil.

- administrador do IdP: cria, protege e revoga a identidade externa;
- administrador de acesso do tenant: opera onboarding/offboarding com
  `identity.manage`;
- aprovador independente: confere tenant, empresas, papel, motivo e evidência;
- auditor: consulta AuditEvent sem alterar o histórico.

Quando a equipe permitir, quem solicita não deve aprovar a própria concessão.
Papéis de proposta e aprovação contábil permanecem separados.

## Pré-requisitos

1. IdP homologado com MFA e access token JWT RS256.
2. Issuer, audience e JWKS HTTPS configurados por secret/configuração de deploy.
3. Claim `tenant_id` emitido apenas pela política confiável do IdP.
4. Migration `20260908_0010` ensaiada no Lab e aplicada por upgrade no Runtime.
5. Tenant, empresas, papel e permissões previamente aprovados e ativos.
6. Backup pré-migration validado conforme o runbook de backup/restore.

Nunca copie token, subject, email, URL de banco ou credencial para ticket, log ou
documentação. Registre apenas IDs internos necessários, decisão e correlação.

## Bootstrap do primeiro administrador

A API não permite autoinscrição e a migration não concede privilégio
automaticamente. Isso é intencional.

O primeiro administrador deve ser vinculado em janela controlada por uma
operação de dados revisada por duas pessoas, com estes guards:

1. confirmar ambiente, `SELECT DATABASE()` e revision Alembic;
2. confirmar no IdP o issuer e o `sub` do administrador sem registrar token;
3. confirmar que o tenant possui exatamente o membership administrativo ativo;
4. atualizar somente o par `(provider_issuer, provider_subject)` do usuário
   previamente aprovado;
5. conceder `identity.manage` somente ao papel administrativo tenant-wide;
6. registrar AuditEvent na mesma transação, com motivo e correlation ID;
7. provar login e uma autorização read-only;
8. revogar imediatamente a mudança se qualquer guard divergir.

O script/SQL de bootstrap deve ser preparado para o tenant específico, revisado
e anexado ao change interno protegido; ele não deve ser transformado em migration
global nem conter PII ou credenciais no repositório. Não vincule automaticamente
todos os usuários legados ao issuer novo.

## Onboarding normal

1. Receber solicitação aprovada com tenant, empresas, papel e justificativa.
2. Criar a identidade no IdP, habilitar MFA e obter seu `sub` por canal
   administrativo protegido.
3. Confirmar que o token futuro terá a audience da API e o tenant correto.
4. Como administrador autenticado, chamar:

```http
POST /api/v1/identity/onboarding
Authorization: Bearer <access-token-do-administrador>
Content-Type: application/json

{
  "provider_subject": "<subject-opaco-do-idp>",
  "display_name": "<nome-de-exibicao>",
  "email": "<email-opcional>",
  "relationship_type": "employee",
  "company_ids": ["<uuid-da-empresa>"],
  "role_id": "<uuid-do-papel>",
  "reason": "<solicitacao-aprovada>"
}
```

Não há `tenant_id` no body: ele vem do token do administrador e é revalidado
contra seu membership. Empresas e papel enviados são apenas seletores.

5. Confirmar resposta `201`, AuditEvent `identity.onboarded` e as quantidades de
   CompanyAccess/RoleBinding sem consultar dados de outro tenant.
6. Pedir ao usuário novo token e testar `GET /api/v1/identity/context` para uma
   empresa autorizada e uma negada.
7. Registrar resultado e correlation ID, nunca o token.

`409 identity conflict` indica vínculo ativo já existente. `403 access denied`
é propositalmente genérico; investigue pelos canais administrativos autorizados,
sem testar IDs de outros tenants.

## Alteração de acesso

O endpoint de onboarding não deve ser usado para acumular papéis em membership
ativo. Mudança de empresas, papel ou segregação exige processo de acesso
específico, aprovação e auditoria. Até esse fluxo ser aprovado, faça offboarding
completo e novo onboarding somente se a política do escritório autorizar e após
revisar o impacto histórico.

## Offboarding

1. Revogar ou desabilitar a conta/sessões no IdP imediatamente.
2. Como administrador do mesmo tenant, chamar:

```http
POST /api/v1/identity/users/<user-id-interno>/offboard
Authorization: Bearer <access-token-do-administrador>
Content-Type: application/json

{"reason": "<solicitacao-ou-incidente>"}
```

3. Confirmar resposta `200`, membership, CompanyAccess e RoleBinding revogados,
   e AuditEvent `identity.offboarded`.
4. Confirmar que um token previamente emitido recebe `403 access denied`.
5. Preservar AuditEvent e demais referências históricas; não apagar o usuário.
6. Se houver membership ativo em outro tenant, o usuário global permanece ativo,
   mas perde integralmente o tenant tratado.

Auto-offboarding é negado. Para remover o último administrador, primeiro
onboarde e valide um substituto, obtenha aprovação independente e só então faça
o offboarding pelo substituto.

## Resposta a incidente e rollback

- suspeita de token: revogar sessão/chaves no IdP e desativar vínculos internos;
- indisponibilidade JWKS: a API falha fechada; não habilitar bypass;
- concessão errada: offboarding imediato, preservar auditoria e abrir incidente;
- falha transacional: nenhuma concessão parcial deve permanecer; conferir pelo
  correlation ID e repetir somente após determinar o estado;
- erro de tenant/empresa: não consultar o recurso suspeito por ID; validar a
  solicitação no cadastro administrativo autorizado.

Não faça downgrade no Runtime. Recuperação de migration segue backup + restore.

## Checklist periódico

- reconciliar usuários ativos no IdP com usuários/memberships internos;
- revisar `identity.manage` e bindings tenant-wide;
- revisar memberships, CompanyAccess e RoleBindings expirados/revogados;
- testar token expirado/inválido e usuário desativado;
- testar negação cross-tenant e cross-company;
- conferir alertas de falha JWKS e tentativas negadas;
- amostrar AuditEvents de onboarding/offboarding e respectivos motivos.

