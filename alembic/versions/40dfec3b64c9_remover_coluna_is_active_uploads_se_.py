"""remover_coluna_is_active_uploads_se_existir

Revision ID: 40dfec3b64c9
Revises: bd34ec0c699a
Create Date: 2026-02-11 09:05:48.016373

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '40dfec3b64c9'
down_revision: Union[str, None] = 'bd34ec0c699a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Verificar se a coluna is_active existe antes de tentar remover
    connection = op.get_bind()
    inspector = sa.inspect(connection)
    columns = [col['name'] for col in inspector.get_columns('uploads')]
    
    if 'is_active' in columns:
        # Remover índice se existir
        op.drop_index('ix_uploads_is_active', table_name='uploads', if_exists=True)
        # Remover coluna is_active
        op.drop_column('uploads', 'is_active')


def downgrade() -> None:
    # Adicionar coluna is_active de volta se necessário
    connection = op.get_bind()
    inspector = sa.inspect(connection)
    columns = [col['name'] for col in inspector.get_columns('uploads')]
    
    if 'is_active' not in columns:
        op.add_column('uploads', 
            sa.Column('is_active', sa.Boolean(), nullable=False, server_default='0'))
        op.create_index('ix_uploads_is_active', 'uploads', ['is_active'], unique=False)
