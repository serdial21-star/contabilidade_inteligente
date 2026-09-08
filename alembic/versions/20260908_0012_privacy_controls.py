'''Privacy technical controls; policies default to pending and no deletion path.

Revision ID: 20260908_0012
Revises: 20260908_0011
'''
from collections.abc import Sequence
from alembic import op
import sqlalchemy as sa
from serdial21.bootstrap.database import UTCDateTime
from uuid import NAMESPACE_URL, uuid5

revision: str = '20260908_0012'
down_revision: str | Sequence[str] | None = '20260908_0011'
branch_labels = depends_on = None
OPTIONS = {'mysql_charset': 'utf8mb4', 'mysql_collate': 'utf8mb4_unicode_ci'}
def upgrade() -> None:
 op.create_table('retention_policies',sa.Column('id',sa.Uuid(),primary_key=True),sa.Column('tenant_id',sa.Uuid(),nullable=False),sa.Column('data_category',sa.String(100),nullable=False),sa.Column('retention_days',sa.Integer()),sa.Column('retention_trigger',sa.String(100),nullable=False),sa.Column('legal_basis_status',sa.String(32),nullable=False),sa.Column('destruction_mode',sa.String(64),nullable=False),sa.Column('approval_status',sa.String(32),nullable=False),sa.Column('exceptions',sa.String(500)),sa.Column('legal_hold_applicable',sa.Boolean(),nullable=False),sa.ForeignKeyConstraint(['tenant_id'],['tenants.id']),**OPTIONS)
 op.create_index('ix_retention_policies_category','retention_policies',['tenant_id','data_category'])
 op.create_table('legal_holds',sa.Column('id',sa.Uuid(),primary_key=True),sa.Column('tenant_id',sa.Uuid(),nullable=False),sa.Column('company_id',sa.Uuid()),sa.Column('resource_type',sa.String(100),nullable=False),sa.Column('resource_id',sa.Uuid()),sa.Column('reason_reference',sa.String(500),nullable=False),sa.Column('status',sa.String(32),nullable=False),sa.Column('created_at',UTCDateTime(),nullable=False),sa.Column('created_by',sa.Uuid(),nullable=False),sa.Column('released_at',UTCDateTime()),sa.Column('released_by',sa.Uuid()),sa.ForeignKeyConstraint(['tenant_id','company_id'],['companies.tenant_id','companies.id']),**OPTIONS)
 op.create_index('ix_legal_holds_active','legal_holds',['tenant_id','company_id','resource_type','resource_id','status'])
 op.create_table('data_subject_requests',sa.Column('id',sa.Uuid(),primary_key=True),sa.Column('tenant_id',sa.Uuid(),nullable=False),sa.Column('company_id',sa.Uuid()),sa.Column('subject_reference_hash',sa.String(64),nullable=False),sa.Column('status',sa.String(32),nullable=False),sa.Column('created_at',UTCDateTime(),nullable=False),sa.Column('created_by',sa.Uuid(),nullable=False),sa.Column('verified_by',sa.Uuid()),sa.Column('completed_at',UTCDateTime()),sa.ForeignKeyConstraint(['tenant_id','company_id'],['companies.tenant_id','companies.id']),**OPTIONS)
 op.create_index('ix_dsr_scope_status','data_subject_requests',['tenant_id','company_id','status'])
 permission=sa.table('permissions',sa.column('id',sa.Uuid()),sa.column('code',sa.String()),sa.column('description',sa.String()),sa.column('version',sa.Integer()),sa.column('is_active',sa.Boolean()))
 codes=('privacy.dsr.manage','privacy.dsr.search','privacy.dsr.export','privacy.retention.evaluate','privacy.legal_hold.manage')
 op.bulk_insert(permission,[{'id':uuid5(NAMESPACE_URL,f'serdial21:permission:v1:{code}'),'code':code,'description':code,'version':1,'is_active':True} for code in codes])
def downgrade() -> None:
 op.execute(sa.text("DELETE FROM permissions WHERE code LIKE 'privacy.%' AND version=1"))
 op.drop_index('ix_dsr_scope_status',table_name='data_subject_requests');op.drop_table('data_subject_requests');op.drop_index('ix_legal_holds_active',table_name='legal_holds');op.drop_table('legal_holds');op.drop_index('ix_retention_policies_category',table_name='retention_policies');op.drop_table('retention_policies')
