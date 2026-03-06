"""criar_tabela_liberacoes_complemento

Revision ID: 1e4005e4c722
Revises: 7ccd5539dec
Create Date: 2026-03-06 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import text


# revision identifiers, used by Alembic.
revision: str = '1e4005e4c722'
down_revision: Union[str, None] = '7ccd5539dec'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Criar tabela liberacoes_complemento
    op.create_table(
        'liberacoes_complemento',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('escola_id', sa.Integer(), nullable=False),
        sa.Column('complemento_upload_id', sa.Integer(), nullable=True),
        sa.Column('liberada', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('numero_folha', sa.Integer(), nullable=True),
        sa.Column('data_liberacao', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['escola_id'], ['escolas.id'], ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['complemento_upload_id'], ['complemento_uploads.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('escola_id', 'complemento_upload_id', name='uq_liberacao_complemento_escola_upload')
    )
    
    # Criar índices
    op.create_index(op.f('ix_liberacoes_complemento_id'), 'liberacoes_complemento', ['id'], unique=False)
    op.create_index(op.f('ix_liberacoes_complemento_escola_id'), 'liberacoes_complemento', ['escola_id'], unique=False)
    op.create_index(op.f('ix_liberacoes_complemento_complemento_upload_id'), 'liberacoes_complemento', ['complemento_upload_id'], unique=False)
    op.create_index(op.f('ix_liberacoes_complemento_liberada'), 'liberacoes_complemento', ['liberada'], unique=False)
    op.create_index(op.f('ix_liberacoes_complemento_numero_folha'), 'liberacoes_complemento', ['numero_folha'], unique=False)


def downgrade() -> None:
    # Remover índices
    op.drop_index(op.f('ix_liberacoes_complemento_numero_folha'), table_name='liberacoes_complemento', if_exists=True)
    op.drop_index(op.f('ix_liberacoes_complemento_liberada'), table_name='liberacoes_complemento', if_exists=True)
    op.drop_index(op.f('ix_liberacoes_complemento_complemento_upload_id'), table_name='liberacoes_complemento', if_exists=True)
    op.drop_index(op.f('ix_liberacoes_complemento_escola_id'), table_name='liberacoes_complemento', if_exists=True)
    op.drop_index(op.f('ix_liberacoes_complemento_id'), table_name='liberacoes_complemento', if_exists=True)
    
    # Remover tabela
    op.drop_table('liberacoes_complemento')
