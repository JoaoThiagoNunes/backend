"""adicionar_codigo_ept_escolas

Revision ID: 4718ca80804d
Revises: 
Create Date: 2025-12-04 16:17:55.435425

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '4718ca80804d'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('escolas', 
        sa.Column('codigo_ept', sa.String(length=5), nullable=True))
    op.create_index(op.f('ix_escolas_codigo_ept'), 'escolas', ['codigo_ept'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_escolas_codigo_ept'), table_name='escolas')
    op.drop_column('escolas', 'codigo_ept')

