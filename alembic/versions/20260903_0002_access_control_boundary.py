'''access control boundary

Revision ID: 20260903_0002
Revises: 20260903_0001
Create Date: 2026-09-03
'''

from collections.abc import Sequence
from uuid import NAMESPACE_URL, UUID, uuid5

from alembic import op
import sqlalchemy as sa


revision: str = '20260903_0002'
down_revision: str | Sequence[str] | None = '20260903_0001'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

TABLE_OPTIONS = {
    'mysql_charset': 'utf8mb4',
    'mysql_collate': 'utf8mb4_unicode_ci',
}

PERMISSIONS = (
    'company.read',
    'company.manage',
    'journal.read',
    'journal.propose',
    'journal.approve',
    'reconciliation.manage',
    'lock.manage',
    'export.execute',
    'audit.read',
)


def permission_id(code: str) -> UUID:
    return uuid5(NAMESPACE_URL, f'serdial21:permission:v1:{code}')


def upgrade() -> None:
    op.create_table(
        'users',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('provider_subject', sa.String(length=255), nullable=False),
        sa.Column('display_name', sa.String(length=200), nullable=False),
        sa.Column('email', sa.String(length=320), nullable=True),
        sa.Column(
            'is_active',
            sa.Boolean(),
            server_default=sa.text('1'),
            nullable=False,
        ),
        sa.Column(
            'created_at',
            sa.DateTime(timezone=True),
            server_default=sa.text('CURRENT_TIMESTAMP'),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_users')),
        sa.UniqueConstraint(
            'provider_subject',
            name='uq_users_provider_subject',
        ),
        **TABLE_OPTIONS,
    )

    permissions_table = op.create_table(
        'permissions',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('code', sa.String(length=100), nullable=False),
        sa.Column('description', sa.String(length=255), nullable=False),
        sa.Column('version', sa.Integer(), nullable=False),
        sa.Column(
            'is_active',
            sa.Boolean(),
            server_default=sa.text('1'),
            nullable=False,
        ),
        sa.Column(
            'created_at',
            sa.DateTime(timezone=True),
            server_default=sa.text('CURRENT_TIMESTAMP'),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_permissions')),
        sa.UniqueConstraint(
            'code',
            'version',
            name='uq_permissions_code_version',
        ),
        **TABLE_OPTIONS,
    )
    op.bulk_insert(
        permissions_table,
        [
            {
                'id': permission_id(code),
                'code': code,
                'description': code,
                'version': 1,
                'is_active': True,
            }
            for code in PERMISSIONS
        ],
    )

    op.create_table(
        'tenant_memberships',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('tenant_id', sa.Uuid(), nullable=False),
        sa.Column('user_id', sa.Uuid(), nullable=False),
        sa.Column('status', sa.String(length=32), nullable=False),
        sa.Column('relationship_type', sa.String(length=64), nullable=False),
        sa.Column('valid_from', sa.DateTime(timezone=True), nullable=False),
        sa.Column('valid_until', sa.DateTime(timezone=True), nullable=True),
        sa.Column('revision', sa.Integer(), nullable=False),
        sa.Column(
            'created_at',
            sa.DateTime(timezone=True),
            server_default=sa.text('CURRENT_TIMESTAMP'),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ['tenant_id'],
            ['tenants.id'],
            name=op.f('fk_tenant_memberships_tenant_id_tenants'),
        ),
        sa.ForeignKeyConstraint(
            ['user_id'],
            ['users.id'],
            name=op.f('fk_tenant_memberships_user_id_users'),
        ),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_tenant_memberships')),
        sa.UniqueConstraint(
            'tenant_id',
            'id',
            name='uq_tenant_memberships_tenant_id_id',
        ),
        **TABLE_OPTIONS,
    )
    op.create_index(
        'ix_tenant_memberships_tenant_user_status',
        'tenant_memberships',
        ['tenant_id', 'user_id', 'status'],
        unique=False,
    )

    op.create_table(
        'companies',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('tenant_id', sa.Uuid(), nullable=False),
        sa.Column('legal_name', sa.String(length=200), nullable=False),
        sa.Column('trade_name', sa.String(length=200), nullable=True),
        sa.Column('tax_identifier', sa.String(length=32), nullable=False),
        sa.Column('timezone', sa.String(length=64), nullable=False),
        sa.Column('currency_code', sa.String(length=3), nullable=False),
        sa.Column('status', sa.String(length=32), nullable=False),
        sa.Column('valid_from', sa.DateTime(timezone=True), nullable=False),
        sa.Column('valid_until', sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            'created_at',
            sa.DateTime(timezone=True),
            server_default=sa.text('CURRENT_TIMESTAMP'),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ['tenant_id'],
            ['tenants.id'],
            name=op.f('fk_companies_tenant_id_tenants'),
        ),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_companies')),
        sa.UniqueConstraint(
            'tenant_id',
            'id',
            name='uq_companies_tenant_id_id',
        ),
        sa.UniqueConstraint(
            'tenant_id',
            'tax_identifier',
            name='uq_companies_tenant_tax_identifier',
        ),
        **TABLE_OPTIONS,
    )

    op.create_table(
        'roles',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('tenant_id', sa.Uuid(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('purpose', sa.String(length=500), nullable=True),
        sa.Column(
            'is_active',
            sa.Boolean(),
            server_default=sa.text('1'),
            nullable=False,
        ),
        sa.Column(
            'created_at',
            sa.DateTime(timezone=True),
            server_default=sa.text('CURRENT_TIMESTAMP'),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ['tenant_id'],
            ['tenants.id'],
            name=op.f('fk_roles_tenant_id_tenants'),
        ),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_roles')),
        sa.UniqueConstraint('tenant_id', 'id', name='uq_roles_tenant_id_id'),
        sa.UniqueConstraint('tenant_id', 'name', name='uq_roles_tenant_name'),
        **TABLE_OPTIONS,
    )

    op.create_table(
        'establishments',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('tenant_id', sa.Uuid(), nullable=False),
        sa.Column('company_id', sa.Uuid(), nullable=False),
        sa.Column('name', sa.String(length=200), nullable=False),
        sa.Column('tax_identifier', sa.String(length=32), nullable=False),
        sa.Column('status', sa.String(length=32), nullable=False),
        sa.Column('valid_from', sa.DateTime(timezone=True), nullable=False),
        sa.Column('valid_until', sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            'created_at',
            sa.DateTime(timezone=True),
            server_default=sa.text('CURRENT_TIMESTAMP'),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ['tenant_id', 'company_id'],
            ['companies.tenant_id', 'companies.id'],
            name='fk_establishments_tenant_company',
        ),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_establishments')),
        sa.UniqueConstraint(
            'tenant_id',
            'company_id',
            'tax_identifier',
            name='uq_establishments_tenant_company_tax_identifier',
        ),
        **TABLE_OPTIONS,
    )

    op.create_table(
        'company_accesses',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('tenant_id', sa.Uuid(), nullable=False),
        sa.Column('membership_id', sa.Uuid(), nullable=False),
        sa.Column('company_id', sa.Uuid(), nullable=False),
        sa.Column('status', sa.String(length=32), nullable=False),
        sa.Column('reason', sa.String(length=500), nullable=True),
        sa.Column('valid_from', sa.DateTime(timezone=True), nullable=False),
        sa.Column('valid_until', sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            'created_at',
            sa.DateTime(timezone=True),
            server_default=sa.text('CURRENT_TIMESTAMP'),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ['tenant_id', 'company_id'],
            ['companies.tenant_id', 'companies.id'],
            name='fk_company_accesses_tenant_company',
        ),
        sa.ForeignKeyConstraint(
            ['tenant_id', 'membership_id'],
            ['tenant_memberships.tenant_id', 'tenant_memberships.id'],
            name='fk_company_accesses_tenant_membership',
        ),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_company_accesses')),
        **TABLE_OPTIONS,
    )
    op.create_index(
        'ix_company_accesses_membership_company_status',
        'company_accesses',
        ['tenant_id', 'membership_id', 'company_id', 'status'],
        unique=False,
    )

    op.create_table(
        'role_permissions',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('tenant_id', sa.Uuid(), nullable=False),
        sa.Column('role_id', sa.Uuid(), nullable=False),
        sa.Column('permission_id', sa.Uuid(), nullable=False),
        sa.Column(
            'created_at',
            sa.DateTime(timezone=True),
            server_default=sa.text('CURRENT_TIMESTAMP'),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ['permission_id'],
            ['permissions.id'],
            name=op.f('fk_role_permissions_permission_id_permissions'),
        ),
        sa.ForeignKeyConstraint(
            ['tenant_id', 'role_id'],
            ['roles.tenant_id', 'roles.id'],
            name='fk_role_permissions_tenant_role',
        ),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_role_permissions')),
        sa.UniqueConstraint(
            'tenant_id',
            'role_id',
            'permission_id',
            name='uq_role_permissions_tenant_role_permission',
        ),
        **TABLE_OPTIONS,
    )

    op.create_table(
        'role_bindings',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('tenant_id', sa.Uuid(), nullable=False),
        sa.Column('membership_id', sa.Uuid(), nullable=False),
        sa.Column('role_id', sa.Uuid(), nullable=False),
        sa.Column('company_id', sa.Uuid(), nullable=True),
        sa.Column('status', sa.String(length=32), nullable=False),
        sa.Column('valid_from', sa.DateTime(timezone=True), nullable=False),
        sa.Column('valid_until', sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            'created_at',
            sa.DateTime(timezone=True),
            server_default=sa.text('CURRENT_TIMESTAMP'),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ['tenant_id', 'company_id'],
            ['companies.tenant_id', 'companies.id'],
            name='fk_role_bindings_tenant_company',
        ),
        sa.ForeignKeyConstraint(
            ['tenant_id', 'membership_id'],
            ['tenant_memberships.tenant_id', 'tenant_memberships.id'],
            name='fk_role_bindings_tenant_membership',
        ),
        sa.ForeignKeyConstraint(
            ['tenant_id', 'role_id'],
            ['roles.tenant_id', 'roles.id'],
            name='fk_role_bindings_tenant_role',
        ),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_role_bindings')),
        **TABLE_OPTIONS,
    )
    op.create_index(
        'ix_role_bindings_membership_scope_status',
        'role_bindings',
        ['tenant_id', 'membership_id', 'company_id', 'status'],
        unique=False,
    )


def downgrade() -> None:
    op.drop_table('role_bindings')
    op.drop_table('role_permissions')
    op.drop_table('company_accesses')
    op.drop_table('establishments')
    op.drop_table('roles')
    op.drop_table('companies')
    op.drop_table('tenant_memberships')
    op.drop_table('permissions')
    op.drop_table('users')
