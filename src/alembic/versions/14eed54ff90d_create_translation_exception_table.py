"""create translation_exception table

Revision ID: 14eed54ff90d
Revises: f85dd97bd9f5
Create Date: 2024-04-25 23:57:12.455316

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '14eed54ff90d'
down_revision: Union[str, None] = 'f85dd97bd9f5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'translation_exception',
        sa.Column('translation_exception_id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('tx_ac', sa.Text(), nullable=False),
        sa.Column('start_position', sa.Integer(), nullable=False),
        sa.Column('end_position', sa.Integer(), nullable=False),
        sa.Column('amino_acid', sa.Text(), nullable=False),
        sa.CheckConstraint('start_position <= end_position', name='start_less_than_or_equal_to_end'),
        sa.ForeignKeyConstraint(['tx_ac'], ['uta.transcript.ac'], onupdate='CASCADE', ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('translation_exception_id'),
        schema='uta',
    )


def downgrade() -> None:
    op.drop_table('translation_exception', schema='uta')
