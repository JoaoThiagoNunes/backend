"""criar_contexto_ativo_e_remover_is_active

Revision ID: 0a8da7550ce0
Revises: 454ee1afc0ab
Create Date: 2026-01-26 11:22:21.452195

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0a8da7550ce0'
down_revision: Union[str, None] = '454ee1afc0ab'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Criar tabela contexto_ativo
    op.create_table(
        'contexto_ativo',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('ano_letivo_id', sa.Integer(), nullable=False),
        sa.Column('upload_id', sa.Integer(), nullable=False),
        sa.Column('ativado_em', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['ano_letivo_id'], ['anos_letivos.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['upload_id'], ['uploads.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('ano_letivo_id', name='uq_contexto_ano_letivo')
    )
    op.create_index(op.f('ix_contexto_ativo_id'), 'contexto_ativo', ['id'], unique=False)
    op.create_index(op.f('ix_contexto_ativo_ano_letivo_id'), 'contexto_ativo', ['ano_letivo_id'], unique=True)
    op.create_index(op.f('ix_contexto_ativo_upload_id'), 'contexto_ativo', ['upload_id'], unique=False)
    
    # 2. Migrar dados: criar contexto_ativo para uploads com is_active=True
    # Para cada ano_letivo_id, pegar o upload mais recente com is_active=True
    connection = op.get_bind()
    
    # Verificar se a coluna is_active existe antes de tentar migrar
    inspector = sa.inspect(connection)
    columns = [col['name'] for col in inspector.get_columns('uploads')]
    
    if 'is_active' in columns:
        # Buscar uploads ativos, agrupando por ano_letivo_id e pegando o mais recente
        if connection.dialect.name == 'sqlite':
            # SQLite: usar subquery para pegar o mais recente de cada ano
            connection.execute(sa.text("""
                INSERT INTO contexto_ativo (ano_letivo_id, upload_id, ativado_em)
                SELECT u1.ano_letivo_id, u1.id, datetime('now')
                FROM uploads u1
                WHERE u1.is_active = 1
                AND u1.id = (
                    SELECT u2.id
                    FROM uploads u2
                    WHERE u2.ano_letivo_id = u1.ano_letivo_id
                    AND u2.is_active = 1
                    ORDER BY u2.upload_date DESC
                    LIMIT 1
                )
                GROUP BY u1.ano_letivo_id
            """))
        else:
            # PostgreSQL/outros: usar DISTINCT ON ou window function
            connection.execute(sa.text("""
                INSERT INTO contexto_ativo (ano_letivo_id, upload_id, ativado_em)
                SELECT DISTINCT ON (ano_letivo_id) ano_letivo_id, id, NOW()
                FROM uploads
                WHERE is_active = true
                ORDER BY ano_letivo_id, upload_date DESC
            """))
    
    # 3. Remover coluna is_active de uploads
    op.drop_index('ix_uploads_is_active', table_name='uploads', if_exists=True)
    if 'is_active' in columns:
        op.drop_column('uploads', 'is_active')


def downgrade() -> None:
    # 1. Adicionar coluna is_active de volta
    op.add_column('uploads', 
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='1'))
    op.create_index('ix_uploads_is_active', 'uploads', ['is_active'], unique=False)
    
    # 2. Restaurar is_active=True para uploads que estão no contexto_ativo
    connection = op.get_bind()
    if connection.dialect.name == 'sqlite':
        connection.execute(sa.text("""
            UPDATE uploads
            SET is_active = 1
            WHERE id IN (SELECT upload_id FROM contexto_ativo)
        """))
    else:
        connection.execute(sa.text("""
            UPDATE uploads
            SET is_active = true
            WHERE id IN (SELECT upload_id FROM contexto_ativo)
        """))
    
    # 3. Remover tabela contexto_ativo
    op.drop_index(op.f('ix_contexto_ativo_upload_id'), table_name='contexto_ativo', if_exists=True)
    op.drop_index(op.f('ix_contexto_ativo_ano_letivo_id'), table_name='contexto_ativo', if_exists=True)
    op.drop_index(op.f('ix_contexto_ativo_id'), table_name='contexto_ativo', if_exists=True)
    op.drop_table('contexto_ativo')
