import argparse
import os
from typing import List, Optional
import gzip
from collections import defaultdict
from dataclasses import dataclass

import logging

from uta.formats.exonset import ExonSet, ExonSetWriter

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class GFFRecord:
    seqid: str
    start: int
    end: int
    strand: str
    exon_number: int
    parent_id: str
    transcript_id: str


def _sort_exons(exons: List[GFFRecord]) -> List[GFFRecord]:
    return sorted(exons, key=lambda e: e.exon_number)


def parse_gff_record(line: str) -> Optional[GFFRecord]:
    """Parses a single line from a GFF file and returns a GFFRecord if record is an exon aligned to an NC_ chromosome and has a transcript id starting with NM_ or NR_."""
    # NC_000001.10	BestRefSeq	exon	11874	12227	.	+	.	ID=exon-NR_046018.2-1;Parent=rna-NR_046018.2;Dbxref=GeneID:100287102,Genbank:NR_046018.2,HGNC:HGNC:37102;gbkey=misc_RNA;gene=DDX11L1;product=DEAD/H-box helicase 11 like 1 (pseudogene);pseudo=true;transcript_id=NR_046018.2
    # NC_000001.10	BestRefSeq	exon	12613	12721	.	+	.	ID=exon-NR_046018.2-2;Parent=rna-NR_046018.2;Dbxref=GeneID:100287102,Genbank:NR_046018.2,HGNC:HGNC:37102;gbkey=misc_RNA;gene=DDX11L1;product=DEAD/H-box helicase 11 like 1 (pseudogene);pseudo=true;transcript_id=NR_046018.2
    # NC_000001.10	BestRefSeq	exon	13221	14409	.	+	.	ID=exon-NR_046018.2-3;Parent=rna-NR_046018.2;Dbxref=GeneID:100287102,Genbank:NR_046018.2,HGNC:HGNC:37102;gbkey=misc_RNA;gene=DDX11L1;product=DEAD/H-box helicase 11 like 1 (pseudogene);pseudo=true;transcript_id=NR_046018.2

    fields = line.strip().split("\t")
    if len(fields) != 9:
        raise ValueError(f"Expected 9 tab-separated fields, got {len(fields)}")

    seqid, source, feature, start, end, score, strand, phase, attributes_str = fields

    if feature != "exon" or not seqid.startswith("NC_"):
        return

    attributes = {}
    for attr_str in attributes_str.split(";"):
        if "=" in attr_str:
            key, value = attr_str.split("=")
            attributes[key.lower()] = value

    parent_id = attributes.get("parent")
    transcript_id = attributes.get("transcript_id")
    if (
        not transcript_id
        or (not transcript_id.startswith("NM_") and not transcript_id.startswith("NR_"))
        or not parent_id
    ):
        return
    try:
        exon_number = _get_exon_number_from_id(alignment_id=attributes.get("id"))
    except (ValueError, IndexError):
        raise ValueError(f'Failed to parse exon number from {attributes.get("id")}')

    return GFFRecord(
        seqid=seqid,
        start=int(start),
        end=int(end),
        strand=strand,
        exon_number=exon_number,
        parent_id=parent_id,
        transcript_id=transcript_id,
    )


def _get_exon_number_from_id(alignment_id: str) -> int:
    """
    Pulls the exon number from the alignment id. Expects the id to be in the format
    exon-<transcript_id>-<exon_number>
    """
    return int(alignment_id.split("-")[-1])


def parse_gff_file(file_path: str) -> dict[str, List[GFFRecord]]:
    tx_data = defaultdict(list)
    with gzip.open(file_path, "rt") as f:
        for line in f:
            if line.startswith("#"):
                continue
            try:
                record = parse_gff_record(line)
            except ValueError as e:
                raise Exception(f"Failed at line :{line} with error: {e}")
            if record:
                tx_data[record.parent_id].append(record)
    return {k: _sort_exons(v) for k, v in tx_data.items()}


def get_zero_based_exon_ranges(transcript_exons: List[GFFRecord]) -> str:
    """Convert exon ranges to 0-based half-open format"""
    formatted_exons = []
    for ex in transcript_exons:
        formatted_exons.append(",".join(map(str, (ex.start - 1, ex.end))))
    return ";".join(formatted_exons)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Parse GFF file.")
    parser.add_argument(
        "gff_file", type=argparse.FileType("rb"), help="Path to the gzipped GFF file"
    )
    parser.add_argument(
        "--prefix",
        "-p",
        type=str,
        default="ncbi-gff",
        help="Output filename (default: ncbi-gff)",
    )
    args = parser.parse_args()

    gff_infile = args.gff_file
    exonset_outfile = args.prefix + ".exonset.gz"
    output_file = gzip.open(exonset_outfile + ".tmp", "wt")
    esw = ExonSetWriter(output_file)

    transcript_alignments = parse_gff_file(gff_infile)
    logger.info(
        f"read {len(transcript_alignments)} transcript alignments from {gff_infile}"
    )

    for transcript_exons in transcript_alignments.values():
        exons_se = get_zero_based_exon_ranges(transcript_exons)
        e = transcript_exons[0]
        es = ExonSet(
            tx_ac=e.transcript_id,
            alt_ac=e.seqid,
            method="splign",
            strand=e.strand,
            exons_se_i=exons_se,
        )
        esw.write(es)
    output_file.close()
    os.rename(exonset_outfile + ".tmp", exonset_outfile)
