"""
Download mito fasta and gbff file. Use BioPython to parse the features in the Mitochondrial genbank file to get
the attributes of a region of the genome that correspond to genes along with their attributes. Output gene/tx/alignment
details to intermediate file needed to update UTA database and SeqRepo.

    FEATURES             Location/Qualifiers
     source          1..16569
                     /organism="Homo sapiens"
                     /organelle="mitochondrion"
                     /mol_type="genomic DNA"
                     /isolation_source="caucasian"
                     /db_xref="taxon:9606"
                     /tissue_type="placenta"
                     /country="United Kingdom: Great Britain"
                     /note="this is the rCRS"
     D-loop          complement(join(16024..16569,1..576))
     gene            577..647
                     /gene="TRNF"
                     /nomenclature="Official Symbol: MT-TF | Name:
                     mitochondrially encoded tRNA phenylalanine | Provided by:
                     HGNC:HGNC:7481"
                     /db_xref="GeneID:4558"
                     /db_xref="HGNC:HGNC:7481"
                     /db_xref="MIM:590070"
     tRNA            577..647
                     /gene="TRNF"
                     /product="tRNA-Phe"
                     /note="NAR: 1455"
                     /anticodon=(pos:611..613,aa:Phe,seq:gaa)
                     /codon_recognized="UUC"
                     /db_xref="GeneID:4558"
                     /db_xref="HGNC:HGNC:7481"
                     /db_xref="MIM:590070"
     gene            648..1601
                     /gene="RNR1"
                     /gene_synonym="MTRNR1"
                     /nomenclature="Official Symbol: MT-RNR1 | Name:
                     mitochondrially encoded 12S RNA | Provided by:
                     HGNC:HGNC:7470"
                     /db_xref="GeneID:4549"
                     /db_xref="HGNC:HGNC:7470"
                     /db_xref="MIM:561000"
     rRNA            648..1601
                     /gene="RNR1"
                     /gene_synonym="MTRNR1"
                     /product="s-rRNA"
                     /note="12S rRNA; 12S ribosomal RNA"
                     /db_xref="GeneID:4549"
                     /db_xref="HGNC:HGNC:7470"
                     /db_xref="MIM:561000"
                     ...
"""
import argparse
import dataclasses
import importlib_resources
import logging
import logging.config
from typing import Dict, Optional

from Bio.Seq import Seq
import Bio.SeqIO
from Bio.SeqFeature import SeqFeature
from Bio.SeqRecord import SeqRecord
from bioutils.digests import seq_md5
from more_itertools import first, one

from uta.formats.geneaccessions import GeneAccessions, GeneAccessionsWriter
from uta.formats.seqinfo import SeqInfo, SeqInfoWriter
from uta.formats.txinfo import TxInfo, TxInfoWriter
from uta.formats.exonset import ExonSet, ExonSetWriter
from uta.tools.eutils import download_from_eutils, NcbiFileFormatEnum


@dataclasses.dataclass
class MitoGeneData:
    gene_id: int
    gene_symbol: str
    name: str
    tx_ac: str
    tx_seq: str
    tx_start: int
    tx_end: int
    alt_ac: str
    alt_start: int
    alt_end: int
    strand: str
    origin: str = "NCBI"
    alignment_method: str = "splign"
    transl_table: Optional[str] = None
    transl_except: Optional[str] = None
    pro_ac: Optional[str] = None
    pro_seq: Optional[str] = None

    def exons_se_i(self) -> str:
        return f"{self.tx_start},{self.tx_end}"

    def cds_se_i(self) -> str:
        return self.exons_se_i() if self.pro_ac else ""

    def alt_exons_se_i(self) -> str:
        return f"{self.alt_start},{self.alt_end}"


logging_conf_fn = importlib_resources.files("uta").joinpath("etc/logging.conf")
logging.config.fileConfig(logging_conf_fn)
logging.getLogger().setLevel(logging.INFO)
logger = logging.getLogger(__name__)


def parse_args():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("accession", type=str)
    parser.add_argument("--output-dir", "-o", default=".", type=str)
    return parser.parse_args()


def download_mito_files(output_dir: str, accession: str) -> Dict[str, str]:
    logger.info(f"downloading files for {accession}")
    mt_gb_filepath = f"{output_dir}/{accession}.gbff"
    mt_fa_filepath = f"{output_dir}/{accession}.fna"

    logger.info(f"downloading {NcbiFileFormatEnum.GENBANK} file to {mt_gb_filepath}")
    download_from_eutils(accession, NcbiFileFormatEnum.GENBANK, mt_gb_filepath)

    logger.info(f"downloading {NcbiFileFormatEnum.FASTA} file to {mt_fa_filepath}")
    download_from_eutils(accession, NcbiFileFormatEnum.FASTA, mt_fa_filepath)

    return {"gbff": mt_gb_filepath, "fna": mt_fa_filepath}


def parse_db_xrefs(gb_feature: SeqFeature) -> Dict[str, str]:
    """
    Example:
        Key: db_xref
        Value: ['GeneID:4558', 'HGNC:HGNC:7481', 'MIM:590070']
    """
    return {
        x.partition(":")[0].strip(): x.partition(":")[2].strip()
        for x in gb_feature.qualifiers.get("db_xref", [])
    }


def parse_nomenclature_value(gb_feature: SeqFeature) -> Dict[str, str]:
    """
    Example:
        Key: nomenclature
        Value: ['Official Symbol: MT-TF | Name: mitochondrially encoded tRNA phenylalanine | Provided by: HGNC:HGNC:7481']
    """
    nomenclature_key = "nomenclature"
    nomenclature_results: Dict[str, str] = {}
    if nomenclature_key in gb_feature.qualifiers:
        nomenclature_list = list(
            map(
                lambda x: x.strip(),
                one(gb_feature.qualifiers[nomenclature_key]).split("|"),
            )
        )
        nomenclature_results = {
            x.partition(":")[0].strip(): x.partition(":")[2].strip()
            for x in nomenclature_list
        }

    return nomenclature_results


def get_mito_genes(gbff_filepath: str):
    logger.info(f"processing NCBI GBFF file from {gbff_filepath}")
    with open(gbff_filepath) as fh:
        for record in Bio.SeqIO.parse(fh, "gb"):
            for feature in record.features:
                xrefs = parse_db_xrefs(feature)

                feature_start, feature_end = (
                    feature.location.start,
                    feature.location.end,
                )

                # dependent on feature type, process data and output if appropriate
                if feature.type == "gene":
                    # assert subsequent features represent the same location
                    assert feature_start == feature.location.start
                    assert feature_end == feature.location.end
                    # for gene feature do not yield anything, just set gene level attributes
                    gene_id = int(xrefs["GeneID"])
                    nomenclature = parse_nomenclature_value(feature)
                    hgnc = nomenclature["Official Symbol"]
                    name = nomenclature["Name"]

                elif feature.type in ("tRNA", "rRNA", "CDS"):
                    # assert subsequent features represent the same location and gene
                    assert int(xrefs["GeneID"]) == gene_id
                    assert feature_start == feature.location.start
                    assert feature_end == feature.location.end
                    # if feature type not CDS, set defaults
                    pro_ac = None
                    pro_seq = None
                    transl_table = None
                    transl_except = None

                    # retrieve sequence, and reverse compliment if on reverse strand
                    ac = f"{record.id}_{feature.location.start:05}_{feature.location.end:05}"
                    feature_seq = record.seq[feature_start:feature_end]
                    strand = "+"
                    if feature.location.strand == -1:
                        strand = "-"
                        feature_seq = feature_seq.reverse_complement()

                    if feature.type == "CDS":
                        # override defaults for CDS features
                        pro_ac = one(feature.qualifiers["protein_id"])
                        pro_seq = str(one(feature.qualifiers["translation"]))
                        transl_table = one(feature.qualifiers["transl_table"])
                        if "transl_except" in feature.qualifiers:
                            transl_except = one(feature.qualifiers["transl_except"])

                    # yield gene data
                    yield MitoGeneData(
                        gene_id=gene_id,
                        gene_symbol=hgnc,
                        name=name,
                        tx_ac=ac,
                        tx_seq=str(feature_seq),
                        tx_start=0,
                        tx_end=feature.location.end - feature.location.start,
                        alt_ac=record.id,
                        alt_start=feature_start,
                        alt_end=feature_end,
                        strand=strand,
                        transl_table=transl_table,
                        transl_except=transl_except,
                        pro_ac=pro_ac,
                        pro_seq=pro_seq,
                    )


def main(ncbi_accession: str, output_dir: str):
    # get input files
    input_files = download_mito_files(output_dir=output_dir, accession=ncbi_accession)

    # extract Mitochondrial gene information
    mito_genes = [mg for mf in input_files.values() for mg in get_mito_genes(mf)]
    logger.info(f"found {len(mito_genes)} genes from parsing {input_files['gbff']}")

    # write gene accessions
    with open(f"{output_dir}/{ncbi_accession}.assocacs", "w") as o_file:
        gaw = GeneAccessionsWriter(o_file)
        for mg in mito_genes:
            if mg.pro_ac is not None:
                gaw.write(
                    GeneAccessions(
                        mg.gene_symbol, mg.tx_ac, mg.gene_id, mg.pro_ac, mg.origin
                    )
                )

    # write sequence information
    with open(f"{output_dir}/{ncbi_accession}.seqinfo", "w") as o_file:
        siw = SeqInfoWriter(o_file)
        for mg in mito_genes:
            siw.write(
                SeqInfo(
                    seq_md5(mg.tx_seq),
                    mg.origin,
                    mg.tx_ac,
                    mg.name,
                    len(mg.tx_seq),
                    None,
                )
            )
            if mg.pro_ac is not None:
                siw.write(
                    SeqInfo(
                        seq_md5(mg.pro_seq),
                        mg.origin,
                        mg.pro_ac,
                        mg.name,
                        len(mg.pro_seq),
                        None,
                    )
                )

    # write out transcript sequence fasta files.
    with open(f"{output_dir}/{ncbi_accession}.rna.fna", "w") as o_file:
        for mg in mito_genes:
            record = SeqRecord(
                Seq(mg.tx_seq),
                id=mg.tx_ac,
                description=mg.name,
            )
            o_file.write(record.format("fasta"))

    # write out protein sequence fasta files.
    with open(f"{output_dir}/{ncbi_accession}.protein.faa", "w") as o_file:
        for mg in mito_genes:
            if mg.pro_ac is not None:
                record = SeqRecord(
                    Seq(mg.pro_seq),
                    id=mg.pro_ac,
                    description=mg.name,
                )
                o_file.write(record.format("fasta"))

    # write transcript information
    with open(f"{output_dir}/{ncbi_accession}.txinfo", "w") as o_file:
        tiw = TxInfoWriter(o_file)
        for mg in mito_genes:
            tiw.write(
                TxInfo(
                    mg.origin,
                    mg.tx_ac,
                    mg.gene_id,
                    mg.gene_symbol,
                    mg.cds_se_i(),
                    mg.exons_se_i(),
                )
            )

    # write exonset
    with open(f"{output_dir}/{ncbi_accession}.exonset", "w") as o_file:
        esw = ExonSetWriter(o_file)
        for mg in mito_genes:
            esw.write(
                ExonSet(
                    mg.tx_ac,
                    mg.alt_ac,
                    mg.alignment_method,
                    mg.strand,
                    mg.alt_exons_se_i(),
                )
            )


if __name__ == "__main__":
    args = parse_args()

    main(args.accession, args.output_dir)
