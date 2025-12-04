"""adicionar_codigo_inep_escolas

Revision ID: 112fa5810fe6
Revises: 4718ca80804d
Create Date: 2025-12-04 16:28:57.185129

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '112fa5810fe6'
down_revision: Union[str, None] = '4718ca80804d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('escolas', 
        sa.Column('codigo_inep', sa.String(length=25), nullable=True))
    op.create_index(op.f('ix_escolas_codigo_inep'), 'escolas', ['codigo_inep'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_escolas_codigo_inep'), table_name='escolas')
    op.drop_column('escolas', 'codigo_inep')
