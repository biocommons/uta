"""
Extract and write all files needed by UTA load, except alt accession exonsets (aka, alignments). From a single
GBFF file we can create dna fasta, protein fasta, associated accessions, and txinfo files.
"""
import argparse
import gzip
import importlib_resources
import io
import logging
import logging.config
from collections import Counter
from contextlib import ExitStack
from typing import Iterable

from Bio.Seq import Seq
import Bio.SeqIO
from Bio.SeqRecord import SeqRecord

from uta.formats.geneaccessions import GeneAccessions, GeneAccessionsWriter
from uta.formats.geneinfo import GeneInfo, GeneInfoWriter
from uta.formats.txinfo import TxInfo, TxInfoWriter
from uta.parsers.seqrecord import SeqRecordFacade, SeqRecordFeatureError
from uta.tools.file_utils import open_file


logging_conf_fn = importlib_resources.files("uta").joinpath("etc/logging.conf")
logging.config.fileConfig(logging_conf_fn)
logging.getLogger().setLevel(logging.INFO)
logger = logging.getLogger(__name__)


def parse_args():
    ap = argparse.ArgumentParser(
        description=__doc__,
    )
    ap.add_argument("GBFF_FILES", nargs="+")
    ap.add_argument("--origin", "-o", default="NCBI")
    ap.add_argument("--prefix", "-p", default="")
    ap.add_argument("--output_dir", "-d", default=".", type=str)
    opts = ap.parse_args()
    return opts


def main(gbff_files: Iterable, origin: str, prefix: str, output_dir: str) -> None:
    if prefix:
        prefix = f"{prefix}."

    # setup context managers for file writers
    with ExitStack() as stack:
        # DNA fasta file
        dna_fasta_fh = stack.enter_context(
            io.TextIOWrapper(
                gzip.open(f"{output_dir}/{prefix}rna.fna.gz", "wb"), encoding="utf-8"
            )
        )

        # Protein fasta file
        protein_fasta_fh = stack.enter_context(
            io.TextIOWrapper(
                gzip.open(f"{output_dir}/{prefix}protein.faa.gz", "wb"), encoding="utf-8"
            )
        )

        geneinfo_fh = stack.enter_context(
            io.TextIOWrapper(
                gzip.open(f"{output_dir}/{prefix}geneinfo.gz", "wb"), encoding="utf-8"
            )
        )
        geneinfo_writer = GeneInfoWriter(geneinfo_fh)

        txinfo_fh = stack.enter_context(
            io.TextIOWrapper(
                gzip.open(f"{output_dir}/{prefix}txinfo.gz", "w"), encoding="utf-8"
            )
        )
        txinfo_writer = TxInfoWriter(txinfo_fh)

        assocacs_fh = stack.enter_context(
            io.TextIOWrapper(
                gzip.open(f"{output_dir}/{prefix}assocacs.gz", "w"), encoding="utf-8"
            )
        )
        assocacs_writer = GeneAccessionsWriter(assocacs_fh)

        total_genes = set()
        skipped_ids = set()
        all_prefixes = Counter()
        for gbff_fn in gbff_files:
            logger.info(f"Processing {gbff_fn}")
            gbff_file_handler = stack.enter_context(open_file(gbff_fn))
            i = 0
            genes = set()
            prefixes = Counter()
            for r in Bio.SeqIO.parse(gbff_file_handler, "gb"):
                srf = SeqRecordFacade(r)
                prefixes.update([srf.id[:2]])
                try:
                    fna_record = SeqRecord(
                        Seq(srf.feature_seq), id=srf.id, description=""
                    )
                    dna_fasta_fh.write(fna_record.format("fasta"))

                    geneinfo_writer.write(
                        GeneInfo(
                            gene_id=srf.gene_id,
                            gene_symbol=srf.gene_symbol,
                            tax_id="9606",
                            hgnc=srf.gene_symbol,
                            maploc="",
                            aliases=srf.gene_synonyms,
                            type=srf.gene_type,
                            summary="",
                            descr="",
                            xrefs=srf.db_xrefs,
                        )
                    )

                    txinfo_writer.write(
                        TxInfo(
                            origin=origin,
                            ac=srf.id,
                            gene_id=srf.gene_id,
                            gene_symbol=srf.gene_symbol,
                            cds_se_i=TxInfo.serialize_cds_se_i(srf.cds_se_i),
                            exons_se_i=TxInfo.serialize_exons_se_i(srf.exons_se_i),
                            transl_except=TxInfo.serialize_transl_except(
                                srf.transl_except
                            ),
                        )
                    )

                    # only write cds features for protein-coding transcripts
                    if srf.cds_feature is not None:
                        pro_record = SeqRecord(
                            Seq(srf.cds_translation), id=srf.cds_protein_id, description=srf.cds_product,
                        )
                        protein_fasta_fh.write(pro_record.format("fasta"))

                        assocacs_writer.write(
                            GeneAccessions(
                                origin=origin,
                                gene_id=srf.gene_id,
                                gene_symbol=srf.gene_symbol,
                                tx_ac=srf.id,
                                pro_ac=srf.cds_protein_id,
                            )
                        )

                    genes.add(srf.gene_id)
                    i += 1
                    if i % 5000 == 0:
                        logger.info(f"Processed {i} records")
                except SeqRecordFeatureError as e:
                    logger.error(f"SeqRecordFeatureError processing {sr.id}: {e}")
                    raise
                except ValueError as e:
                    logger.error(f"ValueError processing {sr.id}: {e}")
                    raise

            logger.info(
                "{ng} genes in {fn} ({c})".format(ng=len(genes), fn=gbff_fn, c=prefixes)
            )
            total_genes ^= genes
            all_prefixes += prefixes
        logger.info(
            "{ng} genes in {nf} files ({c})".format(
                ng=len(total_genes), nf=len(gbff_files), c=all_prefixes
            )
        )


if __name__ == "__main__":
    args = parse_args()
    main(args.GBFF_FILES, args.origin, args.prefix, args.output_dir)
