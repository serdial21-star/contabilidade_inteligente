'''persistent account locks

Revision ID: 20260907_0009
Revises: 20260906_0008
'''
from alembic import op
import sqlalchemy as sa
from serdial21.bootstrap.database import UTCDateTime

revision = '20260907_0009'
down_revision = '20260906_0008'
branch_labels = depends_on = None

def upgrade() -> None:
    op.create_table('account_locks',
        sa.Column('id', sa.Uuid(), primary_key=True), sa.Column('tenant_id', sa.Uuid(), nullable=False), sa.Column('company_id', sa.Uuid(), nullable=False),
        sa.Column('scope', sa.String(32), nullable=False), sa.Column('operations', sa.JSON(), nullable=False), sa.Column('reason', sa.String(500), nullable=False), sa.Column('status', sa.String(32), nullable=False),
        sa.Column('account_id', sa.Uuid()), sa.Column('group_id', sa.Uuid()), sa.Column('module', sa.String(100)), sa.Column('competence', sa.Date()), sa.Column('exercise', sa.Integer()),
        sa.Column('released_by', sa.Uuid()), sa.Column('released_at', UTCDateTime()), sa.Column('release_reason', sa.String(500)),
        sa.Column('scope_fingerprint', sa.String(64), nullable=False), sa.Column('active_marker', sa.String(16)), sa.Column('created_at', UTCDateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.ForeignKeyConstraint(['tenant_id','company_id'], ['companies.tenant_id','companies.id'], name='fk_account_locks_tenant_company'),
        sa.UniqueConstraint('tenant_id','company_id','scope_fingerprint','active_marker', name='uq_account_locks_active_scope'),
        mysql_charset='utf8mb4', mysql_collate='utf8mb4_unicode_ci')
    op.create_index('ix_account_locks_scope_status', 'account_locks', ['tenant_id','company_id','status'])

def downgrade() -> None:
    op.drop_table('account_locks')
