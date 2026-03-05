"""limpar_duplicatas_complemento_e_organizar

Revision ID: 7ccd5539dec
Revises: c30103b915a7
Create Date: 2026-03-05 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import text


# revision identifiers, used by Alembic.
revision: str = '7ccd5539dec'
down_revision: Union[str, None] = 'c30103b915a7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Limpa registros duplicados e órfãos nas tabelas de complemento:
    1. Remove ComplementoEscola órfãos (relacionados a ComplementoUpload deletados)
    2. Remove ComplementoEscola duplicados (mesma escola no mesmo complemento_upload)
    3. Remove ComplementoUpload duplicados (mantém apenas o mais recente por upload_base_id + ano_letivo_id)
    4. Remove uploads órfãos criados para upload_complemento_id
    5. Cria constraint unique para prevenir duplicatas de escolas em complemento
    6. Torna upload_complemento_id nullable para permitir futura remoção
    """
    connection = op.get_bind()
    
    # 1. Remover ComplementoEscola órfãos primeiro (evitar problemas de FK)
    # Deletar registros cujo complemento_upload_id não existe mais
    op.execute(text("""
        DELETE FROM complemento_escolas
        WHERE complemento_upload_id NOT IN (
            SELECT id FROM complemento_uploads
        )
    """))
    
    # 2. Remover ComplementoEscola duplicados
    # Para cada combinação de complemento_upload_id + escola_id, manter apenas o mais recente
    op.execute(text("""
        DELETE FROM complemento_escolas
        WHERE id IN (
            SELECT id
            FROM (
                SELECT 
                    id,
                    ROW_NUMBER() OVER (
                        PARTITION BY complemento_upload_id, escola_id 
                        ORDER BY processed_at DESC
                    ) as rn
                FROM complemento_escolas
            ) ranked
            WHERE rn > 1
        )
    """))
    
    # 3. Remover ComplementoUpload duplicados
    # Para cada ano_letivo_id, manter apenas o ComplementoUpload mais recente
    # Isso garante que há apenas um complemento por ano letivo
    op.execute(text("""
        DELETE FROM complemento_uploads
        WHERE id IN (
            SELECT id
            FROM (
                SELECT 
                    id,
                    ROW_NUMBER() OVER (
                        PARTITION BY ano_letivo_id 
                        ORDER BY upload_date DESC
                    ) as rn
                FROM complemento_uploads
            ) ranked
            WHERE rn > 1
        )
    """))
    
    # 4. Remover uploads órfãos criados para upload_complemento_id
    # Identificar uploads cujo filename começa com "complemento_" e não são mais referenciados
    op.execute(text("""
        DELETE FROM uploads
        WHERE filename LIKE 'complemento_%'
        AND id NOT IN (
            SELECT DISTINCT upload_complemento_id 
            FROM complemento_uploads 
            WHERE upload_complemento_id IS NOT NULL
        )
    """))
    
    # 5. Criar constraint unique para prevenir duplicatas de escolas em complemento
    # Verificar se já existe constraint unique em (complemento_upload_id, escola_id)
    result_unique = connection.execute(text("""
        SELECT conname
        FROM pg_constraint
        WHERE conrelid = 'complemento_escolas'::regclass
        AND contype = 'u'
        AND (
            conname = 'uq_complemento_escolas_upload_escola'
            OR (
                pg_get_constraintdef(oid) LIKE '%complemento_upload_id%'
                AND pg_get_constraintdef(oid) LIKE '%escola_id%'
            )
        )
    """))
    
    constraint_exists = result_unique.fetchone() is not None
    
    if not constraint_exists:
        # Verificar se já existe índice unique
        result_index = connection.execute(text("""
            SELECT indexname
            FROM pg_indexes
            WHERE tablename = 'complemento_escolas'
            AND indexdef LIKE '%UNIQUE%'
            AND indexdef LIKE '%complemento_upload_id%'
            AND indexdef LIKE '%escola_id%'
        """))
        
        index_exists = result_index.fetchone() is not None
        
        if not index_exists:
            # Criar constraint unique
            op.create_unique_constraint(
                'uq_complemento_escolas_upload_escola',
                'complemento_escolas',
                ['complemento_upload_id', 'escola_id']
            )
    
    # 6. Tornar upload_complemento_id nullable para permitir futura remoção
    # Verificar se a coluna já é nullable
    result = connection.execute(text("""
        SELECT is_nullable
        FROM information_schema.columns
        WHERE table_name = 'complemento_uploads'
        AND column_name = 'upload_complemento_id'
    """))
    
    column_info = result.fetchone()
    if column_info and column_info[0] == 'NO':
        # Coluna não é nullable, tornar nullable
        op.alter_column(
            'complemento_uploads',
            'upload_complemento_id',
            existing_type=sa.Integer(),
            nullable=True
        )


def downgrade() -> None:
    """
    Reverter mudanças de schema (não há como reverter limpeza de dados).
    Remover constraint unique e tornar upload_complemento_id NOT NULL novamente.
    """
    connection = op.get_bind()
    
    # Remover constraint unique se existir
    result_unique = connection.execute(text("""
        SELECT conname
        FROM pg_constraint
        WHERE conrelid = 'complemento_escolas'::regclass
        AND contype = 'u'
        AND (
            conname = 'uq_complemento_escolas_upload_escola'
            OR (
                pg_get_constraintdef(oid) LIKE '%complemento_upload_id%'
                AND pg_get_constraintdef(oid) LIKE '%escola_id%'
            )
        )
    """))
    
    constraint_row = result_unique.fetchone()
    if constraint_row:
        constraint_name = constraint_row[0]
        op.drop_constraint(
            constraint_name,
            'complemento_escolas',
            type_='unique'
        )
    
    # Verificar se a coluna é nullable
    result = connection.execute(text("""
        SELECT is_nullable
        FROM information_schema.columns
        WHERE table_name = 'complemento_uploads'
        AND column_name = 'upload_complemento_id'
    """))
    
    column_info = result.fetchone()
    if column_info and column_info[0] == 'YES':
        # Coluna é nullable, tornar NOT NULL novamente
        # Primeiro garantir que não há valores NULL
        op.execute(text("""
            UPDATE complemento_uploads
            SET upload_complemento_id = upload_base_id
            WHERE upload_complemento_id IS NULL
        """))
        
        op.alter_column(
            'complemento_uploads',
            'upload_complemento_id',
            existing_type=sa.Integer(),
            nullable=False
        )
