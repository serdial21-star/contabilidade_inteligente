# Correção do downgrade da migration 0002 em MariaDB

Data: 07/09/2026  
Escopo: correção mínima do downgrade de `20260903_0002_access_control_boundary`.
Não inclui homologação integral `base -> head`.

## Erro original e estado encontrado

O downgrade controlado da Execução 27D chegou à revision `20260903_0002` e
falhou ao executar:

```text
DROP INDEX ix_role_bindings_membership_scope_status ON role_bindings
errno 1553: Cannot drop index ... needed in a foreign key constraint
```

A inspeção read-only posterior confirmou `alembic_version=20260903_0002`.
As tabelas de 0002 continuavam presentes: `users`, `permissions`,
`tenant_memberships`, `companies`, `roles`, `establishments`,
`company_accesses`, `role_permissions` e `role_bindings`; as revisions 0003 a
0006 já tinham sido removidas pelo downgrade anterior.

## FK e índice responsáveis

O DDL MariaDB de `role_bindings` confirmou que
`ix_role_bindings_membership_scope_status (tenant_id, membership_id, company_id,
status)` sustenta a FK composta:

```text
fk_role_bindings_tenant_membership
(tenant_id, membership_id)
-> tenant_memberships(tenant_id, id)
```

O índice é criado explicitamente pela revision 0002, mas MariaDB/InnoDB o usa
como índice de suporte para essa FK. As outras FKs de `role_bindings` tinham
índices de suporte próprios.

## Causa raiz

Classificação: **DOWNGRADE_ORDER_ERROR** e
**AUTOMATIC_INDEX_BEHAVIOR_MARIADB**.

O `upgrade()` cria FKs e então o índice de consulta. O `downgrade()` original
tentava remover o índice antes de remover `role_bindings`; essa ordem viola a
dependência física InnoDB. O mesmo padrão poderia afetar o índice de
`company_accesses`. Os nomes reais de FKs no MariaDB correspondem aos nomes
determinísticos declarados na migration; não houve divergência de nomes.

## Correção mínima

O `downgrade()` agora remove somente as tabelas em ordem reversa de dependência:
`role_bindings`, `role_permissions`, `company_accesses`, `establishments`,
`roles`, `companies`, `tenant_memberships`, `permissions` e `users`.
Os índices pertencentes às tabelas são removidos implicitamente pelo
`DROP TABLE`, depois de as FKs dependentes terem deixado de existir.

Não houve mudança no `upgrade()`, nos modelos de autorização, em constraints
tenant/company ou em `FOREIGN_KEY_CHECKS`. A proteção tenant continua sendo
reforçada pelas mesmas FKs compostas e `CompanyAccess`.

É permitido corrigir a própria revision porque o projeto permanece pré-piloto e
a evidência disponível limita a aplicação real ao banco descartável exclusivo
de homologação. Não há evidência de uso bem-sucedido da revision em ambiente
compartilhado. Caso essa evidência apareça, a estratégia deve mudar para uma
migration corretiva compatível, sem reescrever histórico publicado.

## Provas executadas

No MariaDB 11.8.8, banco exclusivo de homologação:

```text
0001 -> upgrade 0002 -> downgrade 0001 -> upgrade 0002
```

O ciclo passou. Após o downgrade, existiam apenas `tenants` e
`alembic_version`; após o re-upgrade, `role_bindings` e as demais estruturas de
0002 foram recriadas. `FOREIGN_KEY_CHECKS` não foi alterado.

Regressão SQLite: `tests/integration/test_migrations.py` e
`tests/security/test_tenant_authorization.py`: **11 passed**.
Teste MariaDB específico: **2 passed**.

## Riscos restantes

O banco está novamente em 0002, não em head. A homologação integral ainda deve
reexecutar `base -> head`, validar 0003–0008, tipos, concorrência, rollback e
auditoria. O downgrade integral até `base` deve ser revalidado após essa
correção antes de ser considerado suportado.
