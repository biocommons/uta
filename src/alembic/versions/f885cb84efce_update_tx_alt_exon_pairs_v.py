"""update tx_alt_exon_pairs_v

Revision ID: f885cb84efce
Revises: 14eed54ff90d
Create Date: 2024-05-07 21:01:03.693969

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f885cb84efce'
down_revision: Union[str, None] = '14eed54ff90d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("DROP VIEW IF EXISTS tx_alt_exon_pairs_v CASCADE;")
    op.execute("""
                CREATE VIEW tx_alt_exon_pairs_v AS
                    SELECT g.symbol, g.symbol as hgnc, g.gene_id,TES.exon_SET_id AS tes_exon_SET_id,
                       AES.exon_SET_id AS aes_exon_SET_id, TES.tx_ac AS tx_ac,AES.alt_ac AS alt_ac,
                       AES.alt_strand,AES.alt_aln_method, TEX.ORD AS ORD,TEX.exon_id AS tx_exon_id,
                       AEX.exon_id AS alt_exon_id, TEX.start_i AS tx_start_i,TEX.END_i AS tx_END_i, 
                       AEX.start_i AS alt_start_i, AEX.END_i AS alt_END_i, EA.exon_aln_id,EA.cigar
                    FROM exon_SET tes
                    JOIN transcript t ON tes.tx_ac=t.ac
                    JOIN gene g ON t.gene_id=g.gene_id
                    JOIN exon_set aes ON tes.tx_ac=aes.tx_ac AND tes.alt_aln_method='transcript' AND aes.alt_aln_method !~ 'transcript'
                    JOIN exon tex ON tes.exon_SET_id=tex.exon_SET_id
                    JOIN exon aex ON aes.exon_SET_id=aex.exon_SET_id AND tex.ORD=aex.ORD
                    LEFT JOIN exon_aln ea ON ea.tx_exon_id=tex.exon_id AND ea.alt_exon_id=AEX.exon_id;
            """)


def downgrade() -> None:
    op.execute("DROP VIEW IF EXISTS tx_alt_exon_pairs_v CASCADE;")
    op.execute("""
                CREATE VIEW tx_alt_exon_pairs_v AS
                    SELECT g.symbol, g.symbol as hgnc, g.gene_id,TES.exon_SET_id AS tes_exon_SET_id,
                       AES.exon_SET_id AS aes_exon_SET_id, TES.tx_ac AS tx_ac,AES.alt_ac AS alt_ac,
                       AES.alt_strand,AES.alt_aln_method, TEX.ORD AS ORD,TEX.exon_id AS tx_exon_id,
                       AEX.exon_id AS alt_exon_id, TEX.start_i AS tx_start_i,TEX.END_i AS tx_END_i, 
                       AEX.start_i AS alt_start_i, AEX.END_i AS alt_END_i, EA.exon_aln_id,EA.cigar
                    FROM exon_SET tes
                    JOIN transcript t ON tes.tx_ac=t.ac
                    JOIN gene g ON t.gene_id=g.gene_id
                    JOIN exon_set aes ON tes.tx_ac=aes.tx_ac AND tes.alt_aln_method='transcript' AND aes.alt_aln_method!='transcript'
                    JOIN exon tex ON tes.exon_SET_id=tex.exon_SET_id
                    JOIN exon aex ON aes.exon_SET_id=aex.exon_SET_id AND tex.ORD=aex.ORD
                    LEFT JOIN exon_aln ea ON ea.tx_exon_id=tex.exon_id AND ea.alt_exon_id=AEX.exon_id;
            """)

