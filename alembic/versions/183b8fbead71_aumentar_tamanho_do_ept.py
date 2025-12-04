"""aumentar tamanho do ept

Revision ID: 183b8fbead71
Revises: 112fa5810fe6
Create Date: 2025-12-04 16:40:53.110215

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '183b8fbead71'
down_revision: Union[str, None] = '112fa5810fe6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column('escolas', 'codigo_ept',
                    existing_type=sa.String(length=5),
                    type_=sa.String(length=50),
                    existing_nullable=True)

def downgrade() -> None:
    op.alter_column('escolas', 'codigo_ept',
                    existing_type=sa.String(length=50),
                    type_=sa.String(length=5),
                    existing_nullable=True)
