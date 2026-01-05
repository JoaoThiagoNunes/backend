"""adicionar profissionalizante_integrado

Revision ID: 6725d8104086
Revises: 183b8fbead71
Create Date: 2026-01-05 08:42:10.939455

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '6725d8104086'
down_revision: Union[str, None] = '183b8fbead71'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('escolas', 
        sa.Column('profissionalizante_integrado', sa.Integer(), 
                  nullable=True, default=0))


def downgrade() -> None:
    op.drop_column('escolas', 'profissionalizante_integrado')
