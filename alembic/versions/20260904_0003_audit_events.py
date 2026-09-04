'''audit events

Revision ID: 20260904_0003
Revises: 20260903_0002
Create Date: 2026-09-04
'''

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = '20260904_0003'
down_revision: str | Sequence[str] | None = '20260903_0002'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    columns = [
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('tenant_id', sa.Uuid(), nullable=False),
        sa.Column('company_id', sa.Uuid(), nullable=True),
        sa.Column('actor_id', sa.Uuid(), nullable=True),
        sa.Column('origin', sa.String(length=32), nullable=False),
        sa.Column('module', sa.String(length=100), nullable=False),
        sa.Column('action', sa.String(length=100), nullable=False),
        sa.Column('subject_type', sa.String(length=100), nullable=False),
        sa.Column('subject_id', sa.Uuid(), nullable=False),
        sa.Column('subject_version', sa.Integer(), nullable=True),
    ]
    columns.extend([
        sa.Column('before_state', sa.JSON(), nullable=True),
        sa.Column('after_state', sa.JSON(), nullable=True),
        sa.Column('reason', sa.String(length=500), nullable=True),
        sa.Column('correlation_id', sa.Uuid(), nullable=False),
        sa.Column('causation_id', sa.Uuid(), nullable=True),
        sa.Column('occurred_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('integrity_hash', sa.String(length=64), nullable=False),
    ])
    op.create_table(
        'audit_events',
        *columns,
        sa.CheckConstraint(
            'origin IN (' + ','.join(chr(39) + value + chr(39) for value in (
                'HUMAN', 'AI', 'RULE_ENGINE', 'IMPORT', 'API',
                'INTEGRATION', 'AUTOMATION',
            )) + ')',
            name=op.f('ck_audit_events_audit_origin'),
        ),
        sa.ForeignKeyConstraint(
            ['tenant_id'],
            ['tenants.id'],
            name=op.f('fk_audit_events_tenant_id_tenants'),
        ),
        sa.ForeignKeyConstraint(
            ['tenant_id', 'company_id'],
            ['companies.tenant_id', 'companies.id'],
            name='fk_audit_events_tenant_company',
        ),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_audit_events')),
        mysql_charset='utf8mb4',
        mysql_collate='utf8mb4_unicode_ci',
    )
    op.create_index(
        'ix_audit_events_tenant_occurred_at',
        'audit_events',
        ['tenant_id', 'occurred_at'],
    )
    op.create_index(
        'ix_audit_events_tenant_company_time',
        'audit_events',
        ['tenant_id', 'company_id', 'occurred_at'],
    )
    op.create_index(
        'ix_audit_events_tenant_correlation',
        'audit_events',
        ['tenant_id', 'correlation_id'],
    )
    op.create_index(
        'ix_audit_events_tenant_subject',
        'audit_events',
        ['tenant_id', 'subject_type', 'subject_id'],
    )


def downgrade() -> None:
    op.drop_table('audit_events')
