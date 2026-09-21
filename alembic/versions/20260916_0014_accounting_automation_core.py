'''Accounting automation core and item-level evidence.

Revision ID: 20260916_0014
Revises: 20260916_0013
'''
from collections.abc import Sequence
from uuid import NAMESPACE_URL, uuid5

from alembic import op
import sqlalchemy as sa

from serdial21.bootstrap.database import UTCDateTime


revision: str = '20260916_0014'
down_revision: str | Sequence[str] | None = '20260916_0013'
branch_labels = depends_on = None
OPTIONS = {'mysql_charset': 'utf8mb4', 'mysql_collate': 'utf8mb4_unicode_ci'}
PERMISSIONS = (
    'company.accounting_profile.manage', 'accounting.rules.manage',
    'accounting.chart.manage', 'accounting.mapping.manage',
    'accounting.classification.review',
)


def upgrade() -> None:
    op.add_column('fiscal_document_items', sa.Column('gtin', sa.String(32)))
    op.add_column('fiscal_document_items', sa.Column('cest', sa.String(16)))
    op.add_column('fiscal_document_items', sa.Column('freight_total', sa.Numeric(20, 2)))
    op.create_index('ix_fiscal_items_product_identity', 'fiscal_document_items',
                    ['tenant_id', 'company_id', 'product_code', 'gtin', 'ncm'])
    op.create_table('company_business_activities',
        sa.Column('id', sa.Uuid(), primary_key=True), sa.Column('tenant_id', sa.Uuid(), nullable=False),
        sa.Column('company_id', sa.Uuid(), nullable=False), sa.Column('cnae_code', sa.String(7), nullable=False),
        sa.Column('description', sa.String(255)), sa.Column('is_primary', sa.Boolean(), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False), sa.Column('active_primary_marker', sa.String(16)),
        sa.Column('effective_from', sa.Date(), nullable=False), sa.Column('effective_to', sa.Date()),
        sa.ForeignKeyConstraint(['tenant_id','company_id'], ['companies.tenant_id','companies.id'], name='fk_company_activities_company'),
        sa.UniqueConstraint('tenant_id','company_id','id', name='uq_company_activities_scope_id'),
        sa.UniqueConstraint('tenant_id','company_id','cnae_code','effective_from', name='uq_company_activities_cnae_effective'),
        sa.UniqueConstraint('tenant_id','company_id','active_primary_marker', name='uq_company_activities_active_primary'), **OPTIONS)
    op.create_index('ix_company_activities_scope_active', 'company_business_activities', ['tenant_id','company_id','is_active'])
    op.create_table('company_accounting_profiles',
        sa.Column('tenant_id', sa.Uuid(), primary_key=True), sa.Column('company_id', sa.Uuid(), primary_key=True),
        sa.Column('business_segment', sa.String(32), nullable=False),
        sa.Column('keeps_inventory', sa.Boolean()), sa.Column('manufactures_goods', sa.Boolean()),
        sa.Column('resells_goods', sa.Boolean()), sa.Column('provides_services', sa.Boolean()),
        sa.Column('uses_cost_centers', sa.Boolean()), sa.Column('uses_projects', sa.Boolean()),
        sa.Column('controls_fixed_assets', sa.Boolean()), sa.Column('capitalization_threshold', sa.Numeric(20,2)),
        sa.Column('minimum_useful_life_months', sa.Integer()), sa.Column('capitalizes_freight_to_inventory', sa.Boolean()),
        sa.Column('auto_proposal_confidence_threshold', sa.String(16), nullable=False),
        sa.Column('version', sa.Integer(), nullable=False), sa.Column('updated_at', UTCDateTime(), nullable=False),
        sa.ForeignKeyConstraint(['tenant_id','company_id'], ['companies.tenant_id','companies.id'], name='fk_company_accounting_profiles_company'), **OPTIONS)
    op.create_table('counterparties',
        sa.Column('id', sa.Uuid(), primary_key=True), sa.Column('tenant_id', sa.Uuid(), nullable=False),
        sa.Column('tax_id', sa.String(32), nullable=False), sa.Column('legal_name', sa.String(255), nullable=False),
        sa.Column('trade_name', sa.String(255)), sa.Column('role', sa.String(16), nullable=False),
        sa.Column('status', sa.String(16), nullable=False),
        sa.UniqueConstraint('tenant_id','id', name='uq_counterparties_tenant_id'),
        sa.UniqueConstraint('tenant_id','tax_id', name='uq_counterparties_tenant_tax'), **OPTIONS)
    op.create_index('ix_counterparties_tenant_role', 'counterparties', ['tenant_id','role'])
    op.create_table('company_item_profiles',
        sa.Column('id', sa.Uuid(), primary_key=True), sa.Column('tenant_id', sa.Uuid(), nullable=False),
        sa.Column('company_id', sa.Uuid(), nullable=False), sa.Column('counterparty_id', sa.Uuid()),
        sa.Column('supplier_product_code', sa.String(100)), sa.Column('gtin', sa.String(32)),
        sa.Column('ncm', sa.String(16)), sa.Column('normalized_description', sa.String(255), nullable=False),
        sa.Column('identity_hash', sa.String(64), nullable=False), sa.Column('preferred_accounting_intent', sa.String(64)),
        sa.Column('occurrence_count', sa.Integer(), nullable=False), sa.Column('approved_count', sa.Integer(), nullable=False),
        sa.Column('last_used_at', UTCDateTime()), sa.Column('status', sa.String(16), nullable=False),
        sa.ForeignKeyConstraint(['tenant_id','company_id'], ['companies.tenant_id','companies.id'], name='fk_company_item_profiles_company'),
        sa.ForeignKeyConstraint(['tenant_id','counterparty_id'], ['counterparties.tenant_id','counterparties.id'], name='fk_company_item_profiles_counterparty'),
        sa.UniqueConstraint('tenant_id','company_id','identity_hash', name='uq_company_item_profiles_identity'), **OPTIONS)
    op.create_index('ix_company_item_profiles_product', 'company_item_profiles', ['tenant_id','company_id','counterparty_id','supplier_product_code','gtin'])
    op.create_table('item_classifications',
        sa.Column('id', sa.Uuid(), primary_key=True), sa.Column('tenant_id', sa.Uuid(), nullable=False),
        sa.Column('company_id', sa.Uuid(), nullable=False), sa.Column('fiscal_document_id', sa.Uuid(), nullable=False),
        sa.Column('fiscal_document_item_id', sa.Uuid(), nullable=False), sa.Column('selected_intent', sa.String(64), nullable=False),
        sa.Column('classification_category', sa.String(100)), sa.Column('confidence_level', sa.String(16), nullable=False),
        sa.Column('status', sa.String(32), nullable=False), sa.Column('rule_version_id', sa.Uuid()),
        sa.Column('classification_version', sa.Integer(), nullable=False),
        sa.Column('created_at', UTCDateTime(), nullable=False, server_default=sa.func.current_timestamp()),
        sa.ForeignKeyConstraint(['tenant_id','company_id','fiscal_document_item_id'], ['fiscal_document_items.tenant_id','fiscal_document_items.company_id','fiscal_document_items.id'], name='fk_item_classifications_fiscal_item'),
        sa.UniqueConstraint('tenant_id','company_id','id', name='uq_item_classifications_scope_id'),
        sa.UniqueConstraint('tenant_id','company_id','fiscal_document_item_id','classification_version', name='uq_item_classifications_item_version'), **OPTIONS)
    op.create_index('ix_item_classifications_review', 'item_classifications', ['tenant_id','company_id','status','confidence_level'])
    op.create_table('classification_evidence',
        sa.Column('id', sa.Uuid(), primary_key=True), sa.Column('tenant_id', sa.Uuid(), nullable=False),
        sa.Column('company_id', sa.Uuid(), nullable=False), sa.Column('classification_id', sa.Uuid(), nullable=False),
        sa.Column('kind', sa.String(32), nullable=False), sa.Column('intent', sa.String(64), nullable=False),
        sa.Column('weight', sa.Integer(), nullable=False), sa.Column('explanation', sa.String(500), nullable=False),
        sa.Column('reference_id', sa.Uuid()),
        sa.ForeignKeyConstraint(['tenant_id','company_id','classification_id'], ['item_classifications.tenant_id','item_classifications.company_id','item_classifications.id'], name='fk_classification_evidence_result'), **OPTIONS)
    op.create_table('classification_feedback',
        sa.Column('id', sa.Uuid(), primary_key=True), sa.Column('tenant_id', sa.Uuid(), nullable=False),
        sa.Column('company_id', sa.Uuid(), nullable=False), sa.Column('classification_id', sa.Uuid(), nullable=False),
        sa.Column('original_intent', sa.String(64), nullable=False), sa.Column('final_intent', sa.String(64), nullable=False),
        sa.Column('decision_type', sa.String(16), nullable=False), sa.Column('apply_scope', sa.String(32), nullable=False),
        sa.Column('actor_id', sa.Uuid(), nullable=False), sa.Column('decided_at', UTCDateTime(), nullable=False),
        sa.ForeignKeyConstraint(['tenant_id','company_id','classification_id'], ['item_classifications.tenant_id','item_classifications.company_id','item_classifications.id'], name='fk_classification_feedback_result'),
        sa.ForeignKeyConstraint(['actor_id'], ['users.id'], name='fk_classification_feedback_actor'), **OPTIONS)
    op.create_index('ix_classification_feedback_item', 'classification_feedback', ['tenant_id','company_id','classification_id'])
    permission = sa.table('permissions', sa.column('id', sa.Uuid()), sa.column('code', sa.String()),
                          sa.column('description', sa.String()), sa.column('version', sa.Integer()),
                          sa.column('is_active', sa.Boolean()))
    op.bulk_insert(permission, [{'id': uuid5(NAMESPACE_URL, f'serdial21:permission:v1:{code}'),
                                 'code': code, 'description': code, 'version': 1, 'is_active': True}
                                for code in PERMISSIONS])


def downgrade() -> None:
    op.execute(sa.text("DELETE FROM permissions WHERE code IN ('company.accounting_profile.manage','accounting.rules.manage','accounting.chart.manage','accounting.mapping.manage','accounting.classification.review') AND version=1"))
    op.drop_table('classification_feedback')
    op.drop_table('classification_evidence')
    op.drop_table('item_classifications')
    op.drop_table('company_item_profiles')
    op.drop_table('counterparties')
    op.drop_table('company_accounting_profiles')
    op.drop_table('company_business_activities')
    op.drop_index('ix_fiscal_items_product_identity', table_name='fiscal_document_items')
    op.drop_column('fiscal_document_items', 'freight_total'); op.drop_column('fiscal_document_items', 'cest'); op.drop_column('fiscal_document_items', 'gtin')
