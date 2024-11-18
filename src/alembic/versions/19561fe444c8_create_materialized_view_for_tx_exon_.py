"""create materialized view for tx_exon_aln_v

Revision ID: 19561fe444c8
Revises: f885cb84efce
Create Date: 2024-05-07 21:59:09.078549

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '19561fe444c8'
down_revision: Union[str, None] = 'f885cb84efce'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("DROP MATERIALIZED VIEW IF EXISTS tx_exon_aln_mv CASCADE;")
    op.execute("""
            CREATE MATERIALIZED VIEW tx_exon_aln_mv AS SELECT * FROM tx_exon_aln_v WITH NO DATA;
            CREATE INDEX tx_exon_aln_mv_tx_alt_ac_ix ON tx_exon_aln_mv(tx_ac, alt_ac, alt_aln_method);
            GRANT SELECT ON tx_exon_set_summary_mv TO public;
            REFRESH MATERIALIZED VIEW tx_exon_aln_mv;
        """)


def downgrade() -> None:
    op.execute("DROP MATERIALIZED VIEW IF EXISTS tx_exon_aln_mv CASCADE;")
