"""criar_tabela_parcelas_complemento

Revision ID: 20260311_114943
Revises: 1e4005e4c722
Create Date: 2026-03-11 11:49:43.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import text


# revision identifiers, used by Alembic.
revision: str = '20260311_114943'
down_revision: Union[str, None] = '1e4005e4c722'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Criar enum para tipo_cota e tipo_ensino se não existirem
    # (assumindo que já existem das migrations anteriores)
    
    # Criar tabela parcelas_complemento
    op.create_table(
        'parcelas_complemento',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('complemento_escola_id', sa.Integer(), nullable=False),
        sa.Column('tipo_cota', sa.Enum('CUSTEIO', 'PROJETO', 'KIT_ESCOLAR', 'UNIFORME', 'MERENDA', 'SALA_RECURSO', 'PREUNI', name='tipocota'), nullable=False),
        sa.Column('numero_parcela', sa.Integer(), nullable=False),
        sa.Column('tipo_ensino', sa.Enum('FUNDAMENTAL', 'MEDIO', name='tipoensino'), nullable=False),
        sa.Column('valor_centavos', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('porcentagem_alunos', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('calculation_version', sa.String(50), nullable=True),
        sa.ForeignKeyConstraint(['complemento_escola_id'], ['complemento_escolas.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('complemento_escola_id', 'tipo_cota', 'numero_parcela', 'tipo_ensino', name='uq_parcela_complemento_escola_cota_parcela_ensino')
    )
    
    # Criar índices
    op.create_index(op.f('ix_parcelas_complemento_id'), 'parcelas_complemento', ['id'], unique=False)
    op.create_index(op.f('ix_parcelas_complemento_complemento_escola_id'), 'parcelas_complemento', ['complemento_escola_id'], unique=False)
    op.create_index(op.f('ix_parcelas_complemento_tipo_cota'), 'parcelas_complemento', ['tipo_cota'], unique=False)
    op.create_index(op.f('ix_parcelas_complemento_numero_parcela'), 'parcelas_complemento', ['numero_parcela'], unique=False)
    op.create_index(op.f('ix_parcelas_complemento_tipo_ensino'), 'parcelas_complemento', ['tipo_ensino'], unique=False)


def downgrade() -> None:
    # Remover índices
    op.drop_index(op.f('ix_parcelas_complemento_tipo_ensino'), table_name='parcelas_complemento', if_exists=True)
    op.drop_index(op.f('ix_parcelas_complemento_numero_parcela'), table_name='parcelas_complemento', if_exists=True)
    op.drop_index(op.f('ix_parcelas_complemento_tipo_cota'), table_name='parcelas_complemento', if_exists=True)
    op.drop_index(op.f('ix_parcelas_complemento_complemento_escola_id'), table_name='parcelas_complemento', if_exists=True)
    op.drop_index(op.f('ix_parcelas_complemento_id'), table_name='parcelas_complemento', if_exists=True)
    
    # Remover tabela
    op.drop_table('parcelas_complemento')
