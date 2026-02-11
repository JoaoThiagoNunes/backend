"""remover_coluna_estado_liberacao_escolas_se_existir

Revision ID: b850ac830681
Revises: 40dfec3b64c9
Create Date: 2026-02-11 09:08:19.275697

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b850ac830681'
down_revision: Union[str, None] = '40dfec3b64c9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Verificar se a coluna estado_liberacao existe antes de tentar remover
    connection = op.get_bind()
    inspector = sa.inspect(connection)
    columns = [col['name'] for col in inspector.get_columns('escolas')]
    
    if 'estado_liberacao' in columns:
        # Remover índice se existir
        op.drop_index('ix_escolas_estado_liberacao', table_name='escolas', if_exists=True)
        # Remover coluna estado_liberacao
        op.drop_column('escolas', 'estado_liberacao')


def downgrade() -> None:
    # Adicionar coluna estado_liberacao de volta se necessário
    connection = op.get_bind()
    inspector = sa.inspect(connection)
    columns = [col['name'] for col in inspector.get_columns('escolas')]
    
    if 'estado_liberacao' not in columns:
        op.add_column('escolas', 
            sa.Column('estado_liberacao', sa.Boolean(), nullable=False, server_default='0'))
        op.create_index('ix_escolas_estado_liberacao', 'escolas', ['estado_liberacao'], unique=False)
