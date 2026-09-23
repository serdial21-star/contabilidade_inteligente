'''Company-scoped external reference for future correlation.

Revision ID: 20260923_0015
Revises: 20260916_0014
'''

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = '20260923_0015'
down_revision: str | Sequence[str] | None = '20260916_0014'
branch_labels = depends_on = None


def upgrade() -> None:
    op.add_column('companies', sa.Column('external_system', sa.String(64), nullable=True))
    op.add_column('companies', sa.Column('external_type', sa.String(64), nullable=True))
    op.add_column('companies', sa.Column('external_id', sa.String(255), nullable=True))
    op.create_index(
        'ux_companies_tenant_external_reference',
        'companies',
        ['tenant_id', 'external_system', 'external_type', 'external_id'],
        unique=True,
    )


def downgrade() -> None:
    op.drop_index('ux_companies_tenant_external_reference', table_name='companies')
    op.drop_column('companies', 'external_id')
    op.drop_column('companies', 'external_type')
    op.drop_column('companies', 'external_system')
