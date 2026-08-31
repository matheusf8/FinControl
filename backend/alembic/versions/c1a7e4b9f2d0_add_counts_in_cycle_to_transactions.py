"""add counts_in_cycle to transactions

Revision ID: c1a7e4b9f2d0
Revises: bfdf7d642875
Create Date: 2026-08-31 12:00:00.000000

Separa "gasto avulso" (dinheiro/débito, controle na aba Semana) do que entra
na fatura/ciclo do Dashboard. `counts_in_cycle=False` = avulso: aparece só na
aba Semana e nunca nos totais do Dashboard.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c1a7e4b9f2d0'
down_revision: Union[str, None] = 'bfdf7d642875'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table('transactions', schema=None) as batch_op:
        batch_op.add_column(
            sa.Column(
                'counts_in_cycle',
                sa.Boolean(),
                nullable=False,
                server_default=sa.true(),
            )
        )


def downgrade() -> None:
    with op.batch_alter_table('transactions', schema=None) as batch_op:
        batch_op.drop_column('counts_in_cycle')
