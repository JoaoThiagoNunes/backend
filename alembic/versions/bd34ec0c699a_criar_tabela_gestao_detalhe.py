"""criar_tabela_gestao_detalhe

Revision ID: bd34ec0c699a
Revises: 587aa0d2e095
Create Date: 2026-02-11 08:58:08.429747

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'bd34ec0c699a'
down_revision: Union[str, None] = '587aa0d2e095'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
