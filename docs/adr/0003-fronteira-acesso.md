# ADR 0003 — Fronteira de tenant e autorização

- Status: aceito para a Execução 03
- Data: 2026-09-03
- Escopo: Tenant, User, TenantMembership, Company, Establishment,
  CompanyAccess, Role, Permission, RolePermission e RoleBinding

## Contexto

O Serdial21 precisa impedir acesso cross-tenant mesmo quando um usuário conhece
IDs válidos. Identidade global não concede acesso. Toda operação empresarial
exige simultaneamente usuário ativo, membership vigente, empresa do tenant,
CompanyAccess vigente e permissão concedida por papel no escopo correto.

Autenticação externa completa não pertence a esta execução.

## Decisão

- Entidades de domínio são dataclasses imutáveis sem dependência de SQLAlchemy.
- Models ORM permanecem privados no adaptador de persistência.
- User é global e contém somente referência ao provedor e dados mínimos; acesso
  nasce exclusivamente de TenantMembership.
- Roles desta etapa são tenant-locais. Papel de sistema fica adiado.
- Permission é global, versionada e representa uma ação atômica no formato
  recurso.ação. Wildcards não são aceitos.
- A migration semeia os nove códigos aprovados com UUIDs determinísticos.
- Estados autorizativos usam o valor active e vigência no intervalo
  fechado-aberto: valid_from menor ou igual ao instante e valid_until ausente
  ou maior que o instante.
- Mais de uma membership ativa simultânea é tratada como ambiguidade e resulta
  em negação.
- RoleBinding sem company_id tem escopo tenant. Em operação de empresa,
  CompanyAccess continua obrigatório mesmo com papel tenant-wide.
- Toda negação pública usa access_denied e não informa se usuário, empresa,
  membership, acesso, papel ou permissão existe em outro tenant.

## Defesa em profundidade

O serviço filtra tenant em todas as consultas. O banco reforça relações
empresariais com FKs compostas tenant+objeto para Establishment, CompanyAccess,
RolePermission e RoleBinding. Exclusões em cascata não foram habilitadas para
evitar perda silenciosa de histórico.

## Migration

A revision 20260903_0002 é aditiva. Ela preserva tenants e cria apenas as nove
entidades restantes desta execução, seus índices, constraints e catálogo
inicial de permissões.

## Limitações deliberadas

- Não há login, senha, token, sessão autenticada ou integração com IdP.
- Não há endpoints CRUD nem telas administrativas.
- Não há papéis padrão ou concessão automática de permissões.
- Criação, revogação e reativação auditadas serão casos de uso próprios.
- Segregação de funções e acesso excepcional de suporte permanecem posteriores.

