"""remover_estado_liberacao_escolas

Revision ID: 587aa0d2e095
Revises: 0a8da7550ce0
Create Date: 2026-01-26 11:24:35.277280

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '587aa0d2e095'
down_revision: Union[str, None] = '0a8da7550ce0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Remover índice se existir
    op.drop_index('ix_escolas_estado_liberacao', table_name='escolas', if_exists=True)
    # Remover coluna estado_liberacao
    op.drop_column('escolas', 'estado_liberacao')


def downgrade() -> None:
    # Adicionar coluna estado_liberacao de volta
    op.add_column('escolas', 
        sa.Column('estado_liberacao', sa.Boolean(), nullable=False, server_default='0'))
    op.create_index('ix_escolas_estado_liberacao', 'escolas', ['estado_liberacao'], unique=False)
