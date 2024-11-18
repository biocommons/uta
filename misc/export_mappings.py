import argparse
import logging
import re
from bioutils.assemblies import make_name_ac_map
from contextlib import ExitStack
from dataclasses import dataclass, field

import psycopg2
import six

import uta

logging.basicConfig(format='%(asctime)s %(levelname)-8s %(message)s', level=logging.INFO, datefmt='%Y-%m-%d %H:%M:%S')
logger = logging.getLogger("export_mappings")


UTA_SCHEMA_VERSION_SQL = """
select value as schema_version
from meta
where key='schema_version';
"""

ASSOCIATED_ACCESSIONS_SQL = """
select aa.tx_ac, aa.pro_ac
from associated_accessions as aa
where aa.tx_ac='{}';
"""

# get_tx_mapping_options
TX_MAPPING_OPTIONS_SQL = """
select distinct tx_ac,alt_ac,alt_aln_method
from tx_exon_aln_v where tx_ac='{}' and exon_aln_id is not NULL
order by alt_ac,alt_aln_method;
"""

# get_tx_info
TX_V1_INFO_SQL = """
select hgnc, cds_start_i, cds_end_i, tx_ac, alt_ac, alt_aln_method
from transcript T
join exon_set ES on T.ac=ES.tx_ac
where tx_ac='{}' and alt_ac='{}' and alt_aln_method='{}';
"""

TX_V2_INFO_SQL = """
select G.hgnc, T.cds_start_i, T.cds_end_i, ES.tx_ac, ES.alt_ac, ES.alt_aln_method
from gene G
join transcript T on G.gene_id=T.gene_id
join exon_set ES on T.ac=ES.tx_ac
where tx_ac='{}' and alt_ac='{}' and alt_aln_method='{}';
"""

EXON_SET_SQL = """
select *
from tx_exon_aln_v
where tx_ac='{}' and alt_ac='{}' and alt_aln_method='{}'
order by alt_start_i;
"""

TX_INDENTITY_SQL = """
select distinct(tx_ac), alt_ac, alt_aln_method, cds_start_i, cds_end_i, lengths, hgnc
from tx_def_summary_v
where tx_ac='{}';
"""


def parse_args():
    parser = argparse.ArgumentParser(
        description="Export transcript alignments for a given genome build from UTA database."
    )
    parser.add_argument("transcripts_file", type=str)
    parser.add_argument("--genome-build", type=str, default="GRCh37.p13")
    parser.add_argument("--db-url", default="postgresql://uta_admin@localhost/uta")
    parser.add_argument("--schema-name", default="uta_20210129")
    return parser.parse_args()


def _get_cursor(con, schema_name):
    cur = con.cursor(cursor_factory=psycopg2.extras.NamedTupleCursor)
    cur.execute(f"set search_path = {schema_name}")
    return cur


def _get_rows(cur, sql):
    cur.execute(sql)
    return cur.fetchall()


def _get_chr_ac_map(genome_build):
    filtered_chr_ac_map = {}

    def_name_ac_map = make_name_ac_map(assy_name=genome_build, primary_only=True)
    for chr_name in list(map(str, range(1, 23))) + ["X", "Y"]:
        filtered_chr_ac_map[chr_name] = def_name_ac_map.get(chr_name)

    return filtered_chr_ac_map


def main(transcripts_file, genome_build, db_url, schema_name):
    logger.info(f"connecting to {db_url}")
    session = uta.connect(db_url)

    con = session.bind.pool.connect()
    cur = _get_cursor(con, schema_name)

    chr_to_acc_dict = _get_chr_ac_map(genome_build=genome_build)

    schema_version = _get_rows(cur, UTA_SCHEMA_VERSION_SQL)[0].schema_version
    if schema_version == "1.1":
        TX_INFO_SQL = TX_V1_INFO_SQL
    else:
        TX_INFO_SQL = TX_V2_INFO_SQL

    # read in transcripts
    transcripts = []
    with open(transcripts_file, "r") as f:
        for line in f:
            if line.startswith("accession"):
                continue
            accession, chrom = line.rstrip("\r\n").split("\t")
            transcripts.append((accession, chrom))

    # setup context managers for file writers
    with ExitStack() as stack:
        # associated acccessions
        assocacs_fh = stack.enter_context(
            open(f"{schema_name}_associated_accessions.tsv", "w")
        )
        assocacs_fh.write("tx_ac\tpro_ac\n")

        # transcript info
        txinfo_fh = stack.enter_context(open(f"{schema_name}_transcript_info.tsv", "w"))
        txinfo_fh.write("hgnc\ttx_ac\tcds_start_i\tcds_end_i\talt_ac\talt_aln_method\n")

        # exon sets
        exons_fh = stack.enter_context(open(f"{schema_name}_exon_sets.tsv", "w"))
        exons_fh.write("hgnc\ttx_ac\talt_ac\talt_aln_method\talt_strand\tords\ttx_ac_se_i\talt_ac_se_i\tcigars\n")

        # transcript identity
        tx_identity_fh = stack.enter_context(
            open(f"{schema_name}_transcript_identity.tsv", "w")
        )

        logger.info("querying database for transcript mappings...")
        for i, (tx_ac, chrom) in enumerate(transcripts):
            assocacs_rows = _get_rows(cur, ASSOCIATED_ACCESSIONS_SQL.format(tx_ac))
            for row in assocacs_rows:
                assocacs_fh.write(f"{row.tx_ac}\t{row.pro_ac}\n")

            alt_ac = chr_to_acc_dict.get(chrom)
            for alt_aln_method in ("splign", "splign-manual"):
                txinfo_rows = _get_rows(
                    cur, TX_INFO_SQL.format(tx_ac, alt_ac, alt_aln_method)
                )
                if txinfo_rows:
                    for row in txinfo_rows:
                        txinfo_fh.write(
                            f"{row.hgnc}\t{row.tx_ac}\t{row.cds_start_i}\t{row.cds_end_i}\t{row.alt_ac}\t{row.alt_aln_method}\n"
                        )
                exons_rows = _get_rows(
                    cur, EXON_SET_SQL.format(tx_ac, alt_ac, alt_aln_method)
                )
                if exons_rows:
                    hgnc = exons_rows[0].hgnc
                    tx_ac = exons_rows[0].tx_ac
                    alt_ac = exons_rows[0].alt_ac
                    alt_aln_method = exons_rows[0].alt_aln_method
                    alt_strand = exons_rows[0].alt_strand
                    ords, tx_ac_se_i, alt_ac_se_i, cigars = [], [], [], []
                    for row in sorted(exons_rows, key=lambda x: x.ord):
                        ords.append(str(row.ord))
                        tx_ac_se_i.append(f"{row.tx_start_i},{row.tx_end_i}")
                        alt_ac_se_i.append(f"{row.alt_start_i},{row.alt_end_i}")
                        cigars.append(row.cigar)
                    exons_fh.write(
                        f"{hgnc}\t{tx_ac}\t{alt_ac}\t{alt_aln_method}\t{alt_strand}\t{';'.join(ords)}\t{';'.join(tx_ac_se_i)}\t{';'.join(alt_ac_se_i)}\t{';'.join(cigars)}\n"
                    )

            if i % 2500 == 0 and i > 0:
                logger.info(f"processed {i} transcripts")


if __name__ == '__main__':
    arguments = parse_args()
    main(arguments.transcripts_file, arguments.genome_build, arguments.db_url, arguments.schema_name)
