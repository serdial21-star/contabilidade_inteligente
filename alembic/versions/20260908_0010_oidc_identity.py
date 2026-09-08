'''OIDC issuer/subject identity and identity administration permission.

Revision ID: 20260908_0010
Revises: 20260907_0009
'''

from collections.abc import Sequence
from uuid import NAMESPACE_URL, uuid5

from alembic import op
import sqlalchemy as sa


revision: str = '20260908_0010'
down_revision: str | Sequence[str] | None = '20260907_0009'
branch_labels = depends_on = None
LEGACY_ISSUER = 'urn:serdial21:legacy'
PERMISSION_CODE = 'identity.manage'


def upgrade() -> None:
    with op.batch_alter_table('users') as batch:
        batch.add_column(
            sa.Column(
                'provider_issuer',
                sa.String(length=255),
                nullable=False,
                server_default=LEGACY_ISSUER,
            )
        )
        batch.drop_constraint('uq_users_provider_subject', type_='unique')
        batch.create_unique_constraint(
            'uq_users_provider_identity',
            ['provider_issuer', 'provider_subject'],
        )
    with op.batch_alter_table('users') as batch:
        batch.alter_column('provider_issuer', server_default=None)

    permission = sa.table(
        'permissions',
        sa.column('id', sa.Uuid()),
        sa.column('code', sa.String()),
        sa.column('description', sa.String()),
        sa.column('version', sa.Integer()),
        sa.column('is_active', sa.Boolean()),
    )
    op.bulk_insert(permission, [{
        'id': uuid5(NAMESPACE_URL, f'serdial21:permission:v1:{PERMISSION_CODE}'),
        'code': PERMISSION_CODE,
        'description': PERMISSION_CODE,
        'version': 1,
        'is_active': True,
    }])


def downgrade() -> None:
    op.execute(
        sa.text('DELETE FROM permissions WHERE code=:code AND version=1')
        .bindparams(code=PERMISSION_CODE)
    )
    with op.batch_alter_table('users') as batch:
        batch.drop_constraint('uq_users_provider_identity', type_='unique')
        batch.create_unique_constraint(
            'uq_users_provider_subject',
            ['provider_subject'],
        )
        batch.drop_column('provider_issuer')
