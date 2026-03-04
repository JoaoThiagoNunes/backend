"""alterar_fks_liberacoes_para_restrict_preservar_liberacoes

Revision ID: alterar_fks_liberacoes_restrict
Revises: b850ac830681
Create Date: 2026-03-03 12:15:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'alterar_fks_liberacoes_restrict'
down_revision: Union[str, None] = 'b850ac830681'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Alterar FK de liberacoes_parcela de CASCADE para RESTRICT
    op.drop_constraint(
        'liberacoes_parcela_escola_id_fkey',
        'liberacoes_parcela',
        type_='foreignkey'
    )
    op.create_foreign_key(
        'liberacoes_parcela_escola_id_fkey',
        'liberacoes_parcela',
        'escolas',
        ['escola_id'],
        ['id'],
        ondelete='RESTRICT'
    )
    
    # Alterar FK de liberacoes_projeto de CASCADE para RESTRICT
    op.drop_constraint(
        'liberacoes_projeto_escola_id_fkey',
        'liberacoes_projeto',
        type_='foreignkey'
    )
    op.create_foreign_key(
        'liberacoes_projeto_escola_id_fkey',
        'liberacoes_projeto',
        'escolas',
        ['escola_id'],
        ['id'],
        ondelete='RESTRICT'
    )


def downgrade() -> None:
    # Reverter FK de liberacoes_projeto de RESTRICT para CASCADE
    op.drop_constraint(
        'liberacoes_projeto_escola_id_fkey',
        'liberacoes_projeto',
        type_='foreignkey'
    )
    op.create_foreign_key(
        'liberacoes_projeto_escola_id_fkey',
        'liberacoes_projeto',
        'escolas',
        ['escola_id'],
        ['id'],
        ondelete='CASCADE'
    )
    
    # Reverter FK de liberacoes_parcela de RESTRICT para CASCADE
    op.drop_constraint(
        'liberacoes_parcela_escola_id_fkey',
        'liberacoes_parcela',
        type_='foreignkey'
    )
    op.create_foreign_key(
        'liberacoes_parcela_escola_id_fkey',
        'liberacoes_parcela',
        'escolas',
        ['escola_id'],
        ['id'],
        ondelete='CASCADE'
    )
