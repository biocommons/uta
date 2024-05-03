"""
To determine the quality of an alignment in UTA this script will compute metrics that can be used to evaluate
the quality of the alignment.

The metrics are:
    seq_length: max(exon.ends_i)
    exon_count: count of exons linked to transcript (from genbank file)
    aligned_exon_count: count of blocks from GFF file
    exon_structure_mismatch: True if exon_count != aligned_exon_count
    matches: count of matching bases between chromosome and transcript within alignment bounds
    mismatches: count of mismatched bases between chromosome and transcript within alignment bounds
    gap_count: count of gaps (indels) between chromosome and transcript sequenceswithin alignment bounds
    aln_length: total number of alignment blocks, includes counts of indel positions
    identity_gapped: matches / aln_length ## not gap compressed identity calculation
    identity_ungapped: matches / (matches + mismatches)
    coverage: (matches + mismatches + deletions) / seq_length

Example:

                    1          11         21         31         41
    Chromo+:  1 CCAGTGTGGC CGATACCCCA GGTTGGC-AC GCATCGTTGC CTTGGTAAGC 49
                |||||||||| |||| |||    ||  || || |||||||||| ||||||||||
    Refseq+:  1 CCAGTGTGGC CGATGCCC-- -GT--GCTAC GCATCGTTGC CTTGGTAAGC 45

    seq_length: 45
    exon_count: 1
    aligned_exon_count: 1
    matches: 43
    mismatches: 1
    gap_count: 3
    aln_length: 43 matches + 1 mismatch + 3bp insertion + 2bp insertion + 1bp deletion = 50
    identity_gapped: 43 / 50 = 0.86
    identity_ungapped: 43 / (43 + 1) = 0.9772
    coverage: (43 + 1 + 1) / 45 = 1.0

Usage:
    python generate_alignment_metrics.py <output_file> --db-url <db_url> --schema-name <schema_name>
"""

import argparse
import logging
import re
from dataclasses import dataclass, field

import psycopg2
import six

import uta


@dataclass
class CigarAln:
    op: str
    length: int


@dataclass
class ExonAln:
    tx_start_i: int
    tx_end_i: int
    alt_start_i: int
    alt_end_i: int
    cigar: str
    cigar_alns: list[CigarAln] = field(default_factory=list)


@dataclass
class TxAln:
    hgnc: str
    tx_ac: str
    seq_length: int
    exon_count: int
    alt_ac: str
    alt_aln_method: str
    alt_strand: int
    aligned_exon_count: int
    exon_alignments: list[ExonAln] = field(default_factory=list)

    @staticmethod
    def metrics_header():
        return "{}\n".format("\t".join([
            "hgnc",
            "tx_ac",
            "seq_length",
            "exon_count",
            "alt_ac",
            "alt_aln_method",
            "alt_strand",
            "aligned_exon_count",
            "exon_structure_mismatch",
            "matches_bps",
            "mismatches_bps",
            "gap_count",
            "deletions_bps",
            "aln_length",
            "identity_gap",
            "identity_ungap",
            "coverage",
        ]))

    def to_metric_output_row(self):
        return "{}\n".format("\t".join(map(str, [
            self.hgnc,
            self.tx_ac,
            self.seq_length,
            self.exon_count,
            self.alt_ac,
            self.alt_aln_method,
            self.alt_strand,
            self.aligned_exon_count,
            not self.exon_count == self.aligned_exon_count,
            self.matches(),
            self.mismatches(),
            self.gap_count(),
            self.deletions(),
            self.aln_length(),
            self.identity_gap(),
            self.identity_ungap(),
            self.coverage(),
        ])))

    def matches(self):
        matches = 0
        for exon_aln in self.exon_alignments:
            for cigar_aln in exon_aln.cigar_alns:
                if cigar_aln.op == MATCH:
                    matches += cigar_aln.length
        return matches

    def mismatches(self):
        mismatches = 0
        for exon_aln in self.exon_alignments:
            for cigar_aln in exon_aln.cigar_alns:
                if cigar_aln.op == MM:
                    mismatches += cigar_aln.length
        return mismatches

    def deletions(self):
        deletions = 0
        for exon_aln in self.exon_alignments:
            for cigar_aln in exon_aln.cigar_alns:
                if cigar_aln.op == DEL:
                    deletions += cigar_aln.length
        return deletions

    def gap_count(self):
        gaps = 0
        for exon_aln in self.exon_alignments:
            for cigar_aln in exon_aln.cigar_alns:
                if cigar_aln.op == DEL or cigar_aln.op == INS:
                    gaps += 1
        return gaps

    def aln_length(self):
        length = 0
        for exon_aln in self.exon_alignments:
            for cigar_aln in exon_aln.cigar_alns:
                length += cigar_aln.length
        return length

    def identity_gap(self):
        return f"{self.matches() / float(self.aln_length()):.6f}"

    def identity_ungap(self):
        return f"{self.matches() / float(self.matches() + self.mismatches()):.6f}"

    def coverage(self):
        return f"{(self.matches() + self.mismatches() + self.deletions()) / float(self.seq_length):.6f}"


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("alignment_metrics")

p = re.compile("\d+[=DIX]")
MATCH = "="
INS = "I"
DEL = "D"
MM = "X"

TX_EXON_SET_SUMMARY_ALL_BUILD37_SQL = """
select *
from uta_20210129b.tx_exon_set_summary_mv as mv
where mv.alt_aln_method in ('splign', 'splign-manual') and mv.tx_ac ~ 'N[MR]_*' and mv.tx_ac !~ '/'
      and mv.alt_ac in ('NC_000001.10', 'NC_000002.11', 'NC_000003.11', 'NC_000004.11', 'NC_000005.9', 'NC_000006.11',
                        'NC_000007.13', 'NC_000008.10', 'NC_000009.11', 'NC_000010.10', 'NC_000011.9', 'NC_000012.11',
                        'NC_000013.10', 'NC_000014.8', 'NC_000015.9', 'NC_000016.9', 'NC_000017.10', 'NC_000018.9',
                        'NC_000019.9', 'NC_000020.10', 'NC_000021.8', 'NC_000022.10', 'NC_000023.10', 'NC_000024.9'
                        );
"""

TX_EXON_SET_SUMMARY_SQL = """
select mv.ends_i[mv.n_exons] as tx_length, *
from uta_20210129b.tx_exon_set_summary_mv as mv
where mv.tx_ac='{tx_ac}' and mv.alt_ac='{alt_ac}' and mv.alt_aln_method='{alt_aln_method}';
"""

TX_EXON_ALN_SQL = """
select v.hgnc, v.tx_ac, v.alt_ac, v.alt_aln_method, v.alt_strand, v.ord, v.tx_start_i, v.tx_end_i,
       v.alt_start_i, v.alt_end_i, v.cigar
from uta_20210129b.tx_exon_aln_v as v
where tx_ac='{tx_ac}' and alt_ac='{alt_ac}' and alt_aln_method='{alt_aln_method}'
order by ord;
"""


def parse_args():
    parser = argparse.ArgumentParser(description="Generate alignment metrics for transcript alignments")
    parser.add_argument("output_file", type=str)
    parser.add_argument("--db-url", default="postgresql://uta_admin@localhost/uta")
    parser.add_argument("--schema-name", default="uta_20210129b")
    return parser.parse_args()


def _get_cursor(con, schema_name):
    cur = con.cursor(cursor_factory=psycopg2.extras.NamedTupleCursor)
    cur.execute("set role uta_admin;")
    cur.execute(f"set search_path = {schema_name}")
    return cur


def _get_alignment(cur, tx_ac, alt_ac, alt_aln_method, aligned_exon_count):
    # get transcript exon count
    cur.execute(
        TX_EXON_SET_SUMMARY_SQL.format(tx_ac=tx_ac, alt_ac=tx_ac, alt_aln_method="transcript")
    )
    row = cur.fetchone()

    if row is None:
        logger.warn(f"no transcript alignment found for {tx_ac} {alt_ac} {alt_aln_method}")
        tx_exon_count = None
    else:
        tx_exon_count = row.n_exons
    tx_seq_length = row.tx_length

    cur.execute(
        TX_EXON_ALN_SQL.format(
            tx_ac=tx_ac, alt_ac=alt_ac, alt_aln_method=alt_aln_method
        )
    )
    rows = cur.fetchall()
    tx_aln = None

    for row in rows:
        if tx_aln is None:
            tx_aln = TxAln(
                hgnc=row.hgnc,
                tx_ac=row.tx_ac,
                seq_length=tx_seq_length,
                exon_count=tx_exon_count,
                alt_ac=row.alt_ac,
                alt_aln_method=row.alt_aln_method,
                alt_strand=row.alt_strand,
                aligned_exon_count=aligned_exon_count,
            )
        exon_aln = ExonAln(
            tx_start_i=row.tx_start_i,
            tx_end_i=row.tx_end_i,
            alt_start_i=row.alt_start_i,
            alt_end_i=row.alt_end_i,
            cigar=row.cigar,
        )
        for match in p.finditer(exon_aln.cigar):
            cigar_aln = CigarAln(op=match.group()[-1], length=int(match.group()[:-1]))
            exon_aln.cigar_alns.append(cigar_aln)
        tx_aln.exon_alignments.append(exon_aln)
    return tx_aln


def main(db_url, schema_name, output_file):
    logger.info(f"connecting to {db_url}")
    session = uta.connect(db_url)

    con = session.bind.pool.connect()
    cur = _get_cursor(con, schema_name)

    # get tx_ac/alt_ac pairs
    tx_alt_ac_pairs = []
    cur.execute(TX_EXON_SET_SUMMARY_ALL_BUILD37_SQL)
    rows = cur.fetchall()

    for row in rows:
        tx_alt_ac_pairs.append((row.tx_ac, row.alt_ac, row.alt_aln_method, row.n_exons))

    logger.info(f"writing metrics to {output_file} for {len(tx_alt_ac_pairs)} transcript alignments")
    with open(output_file, "w") as f_out:
        f_out.write(TxAln.metrics_header())
        i = 0
        for tx_ac, alt_ac, alt_aln_method, aligned_exon_count in tx_alt_ac_pairs:
            tx_aln = _get_alignment(
                cur, tx_ac, alt_ac, alt_aln_method, aligned_exon_count
            )
            f_out.write(tx_aln.to_metric_output_row())
            f_out.flush()
            i += 1
            if i % 500 == 0:
                logger.info(f"  - {i} transcript alignments processed")


if __name__ == "__main__":
    arguments = parse_args()
    main(arguments.db_url, arguments.schema_name, arguments.output_file)
