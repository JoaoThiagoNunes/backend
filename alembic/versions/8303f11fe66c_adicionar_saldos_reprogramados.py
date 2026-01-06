"""adicionar saldos reprogramados

Revision ID: 8303f11fe66c
Revises: 6725d8104086
Create Date: 2026-01-05 14:37:34.760940

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '8303f11fe66c'
down_revision: Union[str, None] = '6725d8104086'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('escolas', 
        sa.Column('saldo_reprogramado_gestao', sa.Float(), 
                  nullable=True, default=0.0))
    op.add_column('escolas', 
        sa.Column('saldo_reprogramado_merenda', sa.Float(), 
                  nullable=True, default=0.0))


def downgrade() -> None:
    op.drop_column('escolas', 'saldo_reprogramado_gestao')
    op.drop_column('escolas', 'saldo_reprogramado_merenda')
