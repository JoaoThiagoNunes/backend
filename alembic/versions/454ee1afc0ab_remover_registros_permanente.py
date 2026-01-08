"""remover_registros_permanente

Revision ID: 454ee1afc0ab
Revises: 8303f11fe66c
Create Date: 2026-01-08 11:05:21.851187

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '454ee1afc0ab'
down_revision: Union[str, None] = '8303f11fe66c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("""
        DELETE FROM parcelas_profin 
        WHERE tipo_cota = 'PERMANENTE'
    """)

    op.drop_column('calculos_profin', 'profin_permanente')

def downgrade() -> None:
    op.add_column('calculos_profin', sa.Column('profin_permanente', sa.Float, default=0.0))
