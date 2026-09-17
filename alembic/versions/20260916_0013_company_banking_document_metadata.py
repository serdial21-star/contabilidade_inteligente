'''Company banking master and receipt-scoped document metadata.

Revision ID: 20260916_0013
Revises: 20260908_0012
'''
from collections.abc import Mapping, Sequence
import json

from alembic import op
import sqlalchemy as sa

from serdial21.bootstrap.database import UTCDateTime


revision: str = '20260916_0013'
down_revision: str | Sequence[str] | None = '20260908_0012'
branch_labels = depends_on = None
OPTIONS = {'mysql_charset': 'utf8mb4', 'mysql_collate': 'utf8mb4_unicode_ci'}


def upgrade() -> None:
    op.add_column('bank_accounts', sa.Column('bank_name', sa.String(120)))
    op.add_column('bank_accounts', sa.Column('nickname', sa.String(120)))
    op.add_column('bank_accounts', sa.Column('status', sa.String(16), nullable=False, server_default='ACTIVE'))
    op.add_column('bank_accounts', sa.Column('updated_at', UTCDateTime()))
    op.create_index('ix_bank_accounts_scope_status', 'bank_accounts', ['tenant_id', 'company_id', 'status'])
    op.create_table(
        'document_metadata',
        sa.Column('id', sa.Uuid(), primary_key=True),
        sa.Column('tenant_id', sa.Uuid(), nullable=False),
        sa.Column('company_id', sa.Uuid(), nullable=False),
        sa.Column('receipt_id', sa.Uuid(), nullable=False),
        sa.Column('document_number', sa.String(100)),
        sa.Column('description', sa.String(500)),
        sa.Column('observation', sa.String(1000)),
        sa.Column('version', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('created_at', UTCDateTime(), nullable=False, server_default=sa.func.current_timestamp()),
        sa.Column('updated_at', UTCDateTime(), nullable=False),
        sa.ForeignKeyConstraint(
            ['tenant_id', 'company_id', 'receipt_id'],
            ['artifact_receipts.tenant_id', 'artifact_receipts.company_id', 'artifact_receipts.id'],
            name='fk_document_metadata_receipt',
        ),
        sa.UniqueConstraint('tenant_id', 'company_id', 'receipt_id', name='uq_document_metadata_receipt'),
        **OPTIONS,
    )
    op.create_index('ix_document_metadata_number', 'document_metadata', ['tenant_id', 'company_id', 'document_number'])
    op.add_column('nfe_journey_checkpoints', sa.Column('account_search', sa.Text()))
    op.add_column('nfe_journey_checkpoints', sa.Column('rule_search', sa.String(255)))
    op.add_column('nfe_journey_checkpoints', sa.Column('source_search', sa.String(100)))
    op.add_column('nfe_journey_checkpoints', sa.Column('accounting_date_index', sa.Date()))
    bind = op.get_bind()
    rule_names_by_scope: dict[tuple[object, object], dict[str, list[str]]] = {}
    catalog_rows = bind.execute(sa.text(
        'SELECT tenant_id, company_id, content FROM production_catalog_versions'
    )).mappings()
    for row in catalog_rows:
        content = _json_object(row['content'])
        scoped_names = rule_names_by_scope.setdefault(
            (row['tenant_id'], row['company_id']), {},
        )
        for rule in content.get('rules') or []:
            rule_id = str(rule.get('id') or '')
            rule_name = str(rule.get('name') or '').strip()
            if rule_id and rule_name:
                names = scoped_names.setdefault(rule_id, [])
                if rule_name not in names:
                    names.append(rule_name)
    rows = bind.execute(sa.text(
        'SELECT id, tenant_id, company_id, snapshot FROM nfe_journey_checkpoints'
    )).mappings()
    for row in rows:
        snapshot = _json_object(row['snapshot'])
        values = _journey_search_values(
            snapshot,
            rule_names_by_scope.get((row['tenant_id'], row['company_id']), {}),
        )
        bind.execute(sa.text(
            'UPDATE nfe_journey_checkpoints SET account_search=:account_search, '
            'rule_search=:rule_search, source_search=:source_search, '
            'accounting_date_index=:accounting_date_index WHERE id=:id'
        ), {'id': row['id'], **values})
    op.create_index('ix_nfe_journey_search_date', 'nfe_journey_checkpoints',
                    ['tenant_id', 'company_id', 'accounting_date_index'])


def downgrade() -> None:
    op.drop_index('ix_nfe_journey_search_date', table_name='nfe_journey_checkpoints')
    op.drop_column('nfe_journey_checkpoints', 'accounting_date_index')
    op.drop_column('nfe_journey_checkpoints', 'source_search')
    op.drop_column('nfe_journey_checkpoints', 'rule_search')
    op.drop_column('nfe_journey_checkpoints', 'account_search')
    op.drop_index('ix_document_metadata_number', table_name='document_metadata')
    op.drop_table('document_metadata')
    op.drop_index('ix_bank_accounts_scope_status', table_name='bank_accounts')
    op.drop_column('bank_accounts', 'updated_at')
    op.drop_column('bank_accounts', 'status')
    op.drop_column('bank_accounts', 'nickname')
    op.drop_column('bank_accounts', 'bank_name')


def _json_object(value: object) -> dict[str, object]:
    if isinstance(value, str):
        decoded = json.loads(value)
        return decoded if isinstance(decoded, dict) else {}
    return value if isinstance(value, dict) else {}


def _journey_search_values(
    snapshot: dict[str, object],
    rule_names: Mapping[str, Sequence[str]] | None = None,
) -> dict[str, object]:
    lines = snapshot.get('lines') or []
    used = {str(line.get('account_version_id')) for line in lines}
    plan = snapshot.get('plan') or {}
    accounts = plan.get('accounts') or []
    account_search = ' '.join(
        f"{item.get('code', '')} {item.get('name', '')}" for item in accounts
        if str(item.get('id')) in used
    ).strip().lower() or None
    evaluation = snapshot.get('evaluation') or {}
    proposal = evaluation.get('proposal') or {}
    rule_id = str(proposal.get('rule_version_id') or '')
    matched_names = rule_names.get(rule_id, ()) if rule_names else ()
    sources = snapshot.get('sources') or []
    revision = snapshot.get('revision') or {}
    return {
        'account_search': account_search,
        'rule_search': ' '.join((rule_id, *matched_names)).strip().lower() or None,
        'source_search': str(sources[0].get('source_type') or '') if sources else None,
        'accounting_date_index': revision.get('accounting_date'),
    }
