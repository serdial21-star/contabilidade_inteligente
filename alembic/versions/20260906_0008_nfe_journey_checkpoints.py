"""Checkpoints aditivos da jornada vertical e índices omitidos na execução 19."""
from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

from serdial21.bootstrap.database import UTCDateTime

revision: str = '20260906_0008'
down_revision: str | Sequence[str] | None = '20260906_0007'
branch_labels = depends_on = None


def upgrade() -> None:
    op.create_table(
        'nfe_journey_checkpoints',
        sa.Column('id', sa.Uuid(), primary_key=True),
        sa.Column('tenant_id', sa.Uuid(), nullable=False),
        sa.Column('company_id', sa.Uuid(), nullable=False),
        sa.Column('journey_id', sa.Uuid(), nullable=False),
        sa.Column('correlation_id', sa.Uuid(), nullable=False),
        sa.Column('idempotency_key', sa.String(128), nullable=False),
        sa.Column('version', sa.Integer(), nullable=False),
        sa.Column('fiscal_document_id', sa.Uuid(), nullable=True),
        sa.Column('export_batch_id', sa.Uuid(), nullable=True),
        sa.Column('status', sa.String(64), nullable=False),
        sa.Column('snapshot', sa.JSON(), nullable=False),
        sa.Column('snapshot_hash', sa.String(64), nullable=False),
        sa.Column('created_at', UTCDateTime(), nullable=False),
        sa.UniqueConstraint('tenant_id', 'company_id', 'journey_id', 'version', name='uq_nfe_journey_version'),
        sa.UniqueConstraint('tenant_id', 'company_id', 'idempotency_key', 'version', name='uq_nfe_journey_key_version'),
        sa.UniqueConstraint('correlation_id', 'version', name='uq_nfe_journey_correlation_version'),
        sa.ForeignKeyConstraint(['tenant_id', 'company_id'], ['companies.tenant_id', 'companies.id']),
        sa.ForeignKeyConstraint(
            ['tenant_id', 'company_id', 'fiscal_document_id'],
            ['fiscal_documents.tenant_id', 'fiscal_documents.company_id', 'fiscal_documents.id'],
        ),
        mysql_charset='utf8mb4', mysql_collate='utf8mb4_unicode_ci',
    )
    op.create_index('ix_nfe_journey_export', 'nfe_journey_checkpoints',
                    ['tenant_id', 'company_id', 'export_batch_id'])
    op.create_index('ix_workflow_cases_scope_correlation', 'workflow_cases',
                    ['tenant_id', 'company_id', 'correlation_id'])
    op.create_index('ix_workflow_work_items_correlation', 'workflow_work_items',
                    ['tenant_id', 'correlation_id'])
    op.create_index('ix_authorized_effects_scope_status', 'authorized_effects',
                    ['tenant_id', 'company_id', 'authorization_status', 'execution_status'])


def downgrade() -> None:
    # Apenas para banco de teste/rollback pré-uso; histórico preenchido é preservado.
    connection = op.get_bind()
    if connection.scalar(sa.text('SELECT COUNT(*) FROM nfe_journey_checkpoints')):
        raise RuntimeError('archive and approve recovery before removing journey history')
    op.drop_index('ix_authorized_effects_scope_status', table_name='authorized_effects')
    op.drop_index('ix_workflow_work_items_correlation', table_name='workflow_work_items')
    op.drop_index('ix_workflow_cases_scope_correlation', table_name='workflow_cases')
    op.drop_index('ix_nfe_journey_export', table_name='nfe_journey_checkpoints')
    op.drop_table('nfe_journey_checkpoints')

