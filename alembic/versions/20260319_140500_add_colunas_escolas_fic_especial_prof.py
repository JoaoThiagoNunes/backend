"""adicionar_colunas_fic_e_especial_profissionalizante_em_escolas

Revision ID: 20260319_140500
Revises: 20260311_114943
Create Date: 2026-03-19 14:05:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "20260319_140500"
down_revision: Union[str, None] = "20260311_114943"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "escolas",
        sa.Column("fic_senac", sa.Integer(), nullable=False, server_default="0"),
    )
    op.add_column(
        "escolas",
        sa.Column(
            "especial_profissionalizante_parcial",
            sa.Integer(),
            nullable=False,
            server_default="0",
        ),
    )
    op.add_column(
        "escolas",
        sa.Column(
            "especial_profissionalizante_integrado",
            sa.Integer(),
            nullable=False,
            server_default="0",
        ),
    )

    op.alter_column("escolas", "fic_senac", server_default=None)
    op.alter_column("escolas", "especial_profissionalizante_parcial", server_default=None)
    op.alter_column("escolas", "especial_profissionalizante_integrado", server_default=None)


def downgrade() -> None:
    op.drop_column("escolas", "especial_profissionalizante_integrado")
    op.drop_column("escolas", "especial_profissionalizante_parcial")
    op.drop_column("escolas", "fic_senac")

