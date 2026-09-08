'''Catálogo operacional persistente e versionado.

Revision ID: 20260908_0011
Revises: 20260908_0010
'''

from collections.abc import Sequence
from uuid import NAMESPACE_URL, uuid5

from alembic import op
import sqlalchemy as sa

from serdial21.bootstrap.database import UTCDateTime


revision: str = '20260908_0011'
down_revision: str | Sequence[str] | None = '20260908_0010'
branch_labels = depends_on = None
TABLE_OPTIONS = {'mysql_charset': 'utf8mb4', 'mysql_collate': 'utf8mb4_unicode_ci'}
PERMISSIONS = ('catalog.manage', 'catalog.review')


def upgrade() -> None:
    op.create_table(
        'production_catalogs',
        sa.Column('id', sa.Uuid(), primary_key=True),
        sa.Column('tenant_id', sa.Uuid(), nullable=False),
        sa.Column('company_id', sa.Uuid(), nullable=False),
        sa.Column('name', sa.String(200), nullable=False),
        sa.Column('created_at', UTCDateTime(), nullable=False,
                  server_default=sa.text('(CURRENT_TIMESTAMP)')),
        sa.ForeignKeyConstraint(
            ['tenant_id', 'company_id'], ['companies.tenant_id', 'companies.id'],
            name='fk_production_catalogs_tenant_company',
        ),
        sa.UniqueConstraint(
            'tenant_id', 'company_id', 'id', name='uq_production_catalogs_scope_id',
        ),
        sa.UniqueConstraint(
            'tenant_id', 'company_id', name='uq_production_catalogs_scope',
        ),
        **TABLE_OPTIONS,
    )
    op.create_table(
        'production_catalog_versions',
        sa.Column('id', sa.Uuid(), primary_key=True),
        sa.Column('tenant_id', sa.Uuid(), nullable=False),
        sa.Column('company_id', sa.Uuid(), nullable=False),
        sa.Column('catalog_id', sa.Uuid(), nullable=False),
        sa.Column('supersedes_version_id', sa.Uuid(), nullable=True),
        sa.Column('version_no', sa.Integer(), nullable=False),
        sa.Column('status', sa.String(16), nullable=False),
        sa.Column('valid_from', sa.Date(), nullable=False),
        sa.Column('valid_to', sa.Date(), nullable=True),
        sa.Column('content', sa.JSON(), nullable=False),
        sa.Column('content_hash', sa.String(64), nullable=False),
        sa.Column('created_by', sa.Uuid(), nullable=False),
        sa.Column('reviewed_by', sa.Uuid(), nullable=True),
        sa.Column('published_by', sa.Uuid(), nullable=True),
        sa.Column('created_at', UTCDateTime(), nullable=False),
        sa.Column('reviewed_at', UTCDateTime(), nullable=True),
        sa.Column('published_at', UTCDateTime(), nullable=True),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], name='fk_catalog_version_creator'),
        sa.ForeignKeyConstraint(['reviewed_by'], ['users.id'], name='fk_catalog_version_reviewer'),
        sa.ForeignKeyConstraint(['published_by'], ['users.id'], name='fk_catalog_version_publisher'),
        sa.ForeignKeyConstraint(
            ['tenant_id', 'company_id'], ['companies.tenant_id', 'companies.id'],
            name='fk_production_catalog_versions_tenant_company',
        ),
        sa.ForeignKeyConstraint(
            ['tenant_id', 'company_id', 'catalog_id'],
            ['production_catalogs.tenant_id', 'production_catalogs.company_id',
             'production_catalogs.id'],
            name='fk_production_catalog_versions_catalog',
        ),
        sa.ForeignKeyConstraint(
            ['tenant_id', 'company_id', 'supersedes_version_id'],
            ['production_catalog_versions.tenant_id',
             'production_catalog_versions.company_id',
             'production_catalog_versions.id'],
            name='fk_production_catalog_versions_supersedes',
        ),
        sa.UniqueConstraint(
            'tenant_id', 'company_id', 'id',
            name='uq_production_catalog_versions_scope_id',
        ),
        sa.UniqueConstraint(
            'tenant_id', 'company_id', 'catalog_id', 'version_no',
            name='uq_production_catalog_versions_number',
        ),
        **TABLE_OPTIONS,
    )
    op.create_index(
        'ix_production_catalog_versions_active', 'production_catalog_versions',
        ['tenant_id', 'company_id', 'status', 'valid_from', 'valid_to'],
    )

    permission = sa.table(
        'permissions', sa.column('id', sa.Uuid()), sa.column('code', sa.String()),
        sa.column('description', sa.String()), sa.column('version', sa.Integer()),
        sa.column('is_active', sa.Boolean()),
    )
    op.bulk_insert(permission, [{
        'id': uuid5(NAMESPACE_URL, f'serdial21:permission:v1:{code}'),
        'code': code, 'description': code, 'version': 1, 'is_active': True,
    } for code in PERMISSIONS])


def downgrade() -> None:
    op.execute(sa.text(
        "DELETE FROM permissions WHERE code IN ('catalog.manage','catalog.review') "
        'AND version=1'
    ))
    op.drop_index(
        'ix_production_catalog_versions_active',
        table_name='production_catalog_versions',
    )
    op.drop_table('production_catalog_versions')
    op.drop_table('production_catalogs')
