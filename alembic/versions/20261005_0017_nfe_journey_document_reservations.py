"""Reserva ativa de jornada por documento fiscal.

Revision ID: 20261005_0017
Revises: 20260923_0016
"""
from datetime import UTC, datetime
from uuid import UUID, uuid4

from alembic import op
import sqlalchemy as sa

from serdial21.bootstrap.database import UTCDateTime


revision = '20261005_0017'
down_revision = '20260923_0016'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'nfe_journey_document_reservations',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('tenant_id', sa.Uuid(), nullable=False),
        sa.Column('company_id', sa.Uuid(), nullable=False),
        sa.Column('fiscal_document_id', sa.Uuid(), nullable=False),
        sa.Column('journey_id', sa.Uuid(), nullable=False),
        sa.Column('active_marker', sa.String(16), nullable=True),
        sa.Column('created_by', sa.Uuid(), nullable=True),
        sa.Column('created_at', UTCDateTime(), nullable=False),
        sa.Column('released_by', sa.Uuid(), nullable=True),
        sa.Column('released_at', UTCDateTime(), nullable=True),
        sa.Column('release_reason', sa.String(32), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint(
            'tenant_id', 'company_id', 'fiscal_document_id', 'active_marker',
            name='uq_nfe_journey_document_active',
        ),
        sa.ForeignKeyConstraint(
            ['tenant_id', 'company_id'], ['companies.tenant_id', 'companies.id'],
            name='fk_nfe_journey_reservation_company',
        ),
        sa.ForeignKeyConstraint(
            ['tenant_id', 'company_id', 'fiscal_document_id'],
            ['fiscal_documents.tenant_id', 'fiscal_documents.company_id', 'fiscal_documents.id'],
            name='fk_nfe_journey_reservation_document',
        ),
        sa.CheckConstraint(
            "active_marker = 'ACTIVE' OR active_marker IS NULL",
            name='ck_nfe_journey_reservation_active',
        ),
        mysql_charset='utf8mb4', mysql_collate='utf8mb4_unicode_ci',
    )
    op.create_index(
        'ix_nfe_journey_reservation_owner', 'nfe_journey_document_reservations',
        ['tenant_id', 'company_id', 'journey_id'], unique=False,
    )
    _backfill_latest_non_rejected()


def _backfill_latest_non_rejected() -> None:
    connection = op.get_bind()
    checkpoints = sa.table(
        'nfe_journey_checkpoints',
        sa.column('tenant_id', sa.Uuid()), sa.column('company_id', sa.Uuid()),
        sa.column('fiscal_document_id', sa.Uuid()), sa.column('journey_id', sa.Uuid()),
        sa.column('version', sa.Integer()), sa.column('status', sa.String()),
        sa.column('created_at', UTCDateTime()), sa.column('snapshot', sa.JSON()),
    )
    reservations = sa.table(
        'nfe_journey_document_reservations',
        sa.column('id', sa.Uuid()), sa.column('tenant_id', sa.Uuid()),
        sa.column('company_id', sa.Uuid()), sa.column('fiscal_document_id', sa.Uuid()),
        sa.column('journey_id', sa.Uuid()), sa.column('active_marker', sa.String()),
        sa.column('created_by', sa.Uuid()), sa.column('created_at', UTCDateTime()),
    )
    rows = connection.execute(sa.select(checkpoints).where(
        checkpoints.c.fiscal_document_id.is_not(None),
    ).order_by(
        checkpoints.c.tenant_id, checkpoints.c.company_id,
        checkpoints.c.fiscal_document_id, checkpoints.c.created_at.desc(),
        checkpoints.c.version.desc(),
    )).mappings()
    selected: set[tuple[object, object, object]] = set()
    seen_journeys: set[tuple[object, object, object]] = set()
    for row in rows:
        journey_key = (row['tenant_id'], row['company_id'], row['journey_id'])
        if journey_key in seen_journeys:
            continue
        seen_journeys.add(journey_key)
        if row['status'] in {'REJECTED', 'SUPERSEDED'}:
            continue
        document_key = (row['tenant_id'], row['company_id'], row['fiscal_document_id'])
        if document_key in selected:
            continue
        selected.add(document_key)
        snapshot = row['snapshot'] or {}
        actor = _snapshot_actor(snapshot)
        connection.execute(reservations.insert().values(
            id=uuid4(), tenant_id=row['tenant_id'], company_id=row['company_id'],
            fiscal_document_id=row['fiscal_document_id'], journey_id=row['journey_id'],
            # NULL significa reserva histórica criada pela migration 0017;
            # nunca se fabrica uma identidade humana ausente do snapshot.
            active_marker='ACTIVE', created_by=actor,
            created_at=row['created_at'] or datetime.now(UTC),
        ))


def _snapshot_actor(snapshot: object) -> UUID | None:
    """Converte o `proposer_id` textual do snapshot JSON; ausente ou inválido vira NULL."""
    raw = snapshot.get('proposer_id') if isinstance(snapshot, dict) else None
    if isinstance(raw, UUID):
        return raw
    try:
        return UUID(str(raw)) if raw else None
    except ValueError:
        return None


def downgrade() -> None:
    op.drop_index('ix_nfe_journey_reservation_owner', table_name='nfe_journey_document_reservations')
    op.drop_table('nfe_journey_document_reservations')
