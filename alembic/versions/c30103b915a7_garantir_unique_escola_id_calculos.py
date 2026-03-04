"""garantir_unique_escola_id_calculos

Revision ID: c30103b915a7
Revises: alterar_fks_liberacoes_restrict
Create Date: 2026-03-04 08:27:02.231320

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import text


# revision identifiers, used by Alembic.
revision: str = 'c30103b915a7'
down_revision: Union[str, None] = 'alterar_fks_liberacoes_restrict'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Garante que existe uma constraint UNIQUE em escola_id na tabela calculos_profin.
    Primeiro verifica se há duplicatas e remove-as (mantendo o mais recente).
    Depois verifica se a constraint já existe e cria se necessário.
    """
    # 1. Verificar e remover duplicatas antes de criar a constraint
    # Manter apenas o cálculo mais recente para cada escola_id
    op.execute("""
        DELETE FROM calculos_profin
        WHERE id IN (
            SELECT id
            FROM (
                SELECT 
                    id,
                    ROW_NUMBER() OVER (
                        PARTITION BY escola_id 
                        ORDER BY calculated_at DESC
                    ) as rn
                FROM calculos_profin
            ) ranked
            WHERE rn > 1
        )
    """)
    
    # 2. Verificar se já existe uma constraint unique em escola_id
    # Buscar constraints unique existentes na tabela
    connection = op.get_bind()
    result = connection.execute(text("""
        SELECT conname
        FROM pg_constraint
        WHERE conrelid = 'calculos_profin'::regclass
        AND contype = 'u'
        AND pg_get_constraintdef(oid) LIKE '%escola_id%'
    """))
    
    constraint_exists = result.fetchone() is not None
    
    # 3. Criar constraint se não existir
    if not constraint_exists:
        # Verificar se já existe algum índice unique (que pode ser usado como constraint)
        result_index = connection.execute(text("""
            SELECT indexname
            FROM pg_indexes
            WHERE tablename = 'calculos_profin'
            AND indexdef LIKE '%UNIQUE%'
            AND indexdef LIKE '%escola_id%'
        """))
        
        index_exists = result_index.fetchone() is not None
        
        if not index_exists:
            # Criar constraint unique
            op.create_unique_constraint(
                'uq_calculos_profin_escola_id',
                'calculos_profin',
                ['escola_id']
            )
        else:
            # Se existe índice unique mas não constraint, criar constraint com mesmo nome do índice
            index_result = connection.execute(text("""
                SELECT indexname
                FROM pg_indexes
                WHERE tablename = 'calculos_profin'
                AND indexdef LIKE '%UNIQUE%'
                AND indexdef LIKE '%escola_id%'
                LIMIT 1
            """))
            index_row = index_result.fetchone()
            if index_row:
                index_name = index_row[0]
                # Criar constraint usando o índice existente
                op.execute(text(f"""
                    ALTER TABLE calculos_profin
                    ADD CONSTRAINT uq_calculos_profin_escola_id
                    UNIQUE USING INDEX {index_name}
                """))


def downgrade() -> None:
    """
    Remove a constraint unique de escola_id se existir.
    """
    # Verificar se a constraint existe antes de tentar remover
    connection = op.get_bind()
    result = connection.execute(text("""
        SELECT conname
        FROM pg_constraint
        WHERE conrelid = 'calculos_profin'::regclass
        AND contype = 'u'
        AND (
            conname = 'uq_calculos_profin_escola_id'
            OR pg_get_constraintdef(oid) LIKE '%escola_id%'
        )
    """))
    
    constraint_name = result.fetchone()
    
    if constraint_name:
        constraint_name = constraint_name[0]
        op.drop_constraint(
            constraint_name,
            'calculos_profin',
            type_='unique'
        )
