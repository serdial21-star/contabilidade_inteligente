'''Equipe interna do escritório e vínculo com empresas (ADR 0013).

Revision ID: 20260923_0016
Revises: 20260923_0015
'''

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = '20260923_0016'
down_revision: str | Sequence[str] | None = '20260923_0015'
branch_labels = depends_on = None

_TABLE_OPTIONS = {'mysql_charset': 'utf8mb4', 'mysql_collate': 'utf8mb4_unicode_ci'}


def upgrade() -> None:
    op.create_table(
        'office_team_members',
        sa.Column('id', sa.Uuid(), primary_key=True),
        sa.Column('tenant_id', sa.Uuid(), sa.ForeignKey('tenants.id'), nullable=False),
        sa.Column('display_name', sa.String(200), nullable=False),
        sa.Column('email', sa.String(255), nullable=True),
        sa.Column('job_title', sa.String(100), nullable=True),
        sa.Column('status', sa.String(32), nullable=False),
        sa.Column('external_system', sa.String(64), nullable=True),
        sa.Column('external_type', sa.String(64), nullable=True),
        sa.Column('external_id', sa.String(255), nullable=True),
        sa.Column('valid_from', sa.DateTime(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False,
                  server_default=sa.func.current_timestamp()),
        sa.UniqueConstraint('tenant_id', 'id', name='uq_office_team_members_tenant_id_id'),
        sa.UniqueConstraint('tenant_id', 'email', name='uq_office_team_members_tenant_email'),
        **_TABLE_OPTIONS,
    )
    op.create_index(
        'ux_office_team_members_tenant_external_reference', 'office_team_members',
        ['tenant_id', 'external_system', 'external_type', 'external_id'], unique=True,
    )
    op.create_table(
        'company_team_assignments',
        sa.Column('id', sa.Uuid(), primary_key=True),
        sa.Column('tenant_id', sa.Uuid(), nullable=False),
        sa.Column('company_id', sa.Uuid(), nullable=False),
        sa.Column('team_member_id', sa.Uuid(), nullable=False),
        sa.Column('role_label', sa.String(64), nullable=False),
        sa.Column('status', sa.String(32), nullable=False),
        sa.Column('valid_from', sa.DateTime(), nullable=False),
        sa.Column('valid_until', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False,
                  server_default=sa.func.current_timestamp()),
        sa.ForeignKeyConstraint(
            ['tenant_id', 'company_id'], ['companies.tenant_id', 'companies.id'],
            name='fk_company_team_assignments_tenant_company',
        ),
        sa.ForeignKeyConstraint(
            ['tenant_id', 'team_member_id'],
            ['office_team_members.tenant_id', 'office_team_members.id'],
            name='fk_company_team_assignments_tenant_member',
        ),
        sa.UniqueConstraint(
            'tenant_id', 'company_id', 'team_member_id', 'role_label',
            name='uq_company_team_assignments_scope',
        ),
        **_TABLE_OPTIONS,
    )


def downgrade() -> None:
    op.drop_table('company_team_assignments')
    op.drop_index('ux_office_team_members_tenant_external_reference',
                  table_name='office_team_members')
    op.drop_table('office_team_members')
