"""read NCBI-flavored TSV files

NCBI TSV files have a header, with columns preceded by "#Format: " and
space-separated, as follows:

    #Format: tax_id GeneID Symbol LocusTag Synonyms dbXrefs chromosome map_location description ...
    9606	1	A1BG	-	A1B|ABG|GAB|HYST2477	MIM:138670|HGNC:HGNC:5|Ensembl:ENSG00000121...

(This is from the top of
ftp://ftp.ncbi.nih.gov/gene/DATA/GENE_INFO/Mammalia/Homo_sapiens.gene_info.gz.)

This module containts a parser (based on csv.DictReader) that returns
rows of such files as dictionaries.

"""

import csv
import re


class NCBITSVReader(object):

    def __init__(self, fd, squash_case=True):
        line1 = fd.readline()
        if not line1.startswith("#"):
            raise RuntimeError("File stream does not begin with '#'")

        hdr = line1.replace("#", "").replace(
            " (tab is used as a separator, pound sign - start of a comment)", "")
        if squash_case:
            hdr = hdr.lower()
        fieldnames = hdr.split()
        self._dr = csv.DictReader(f=fd, fieldnames=fieldnames, delimiter="\t")

    def __iter__(self):
        return self

    def __next__(self):
        return self._dr.__next__()


if __name__ == "__main__":
    from io import StringIO
    from pprint import pprint

    data = """#Format: tax_id GeneID Symbol LocusTag Synonyms dbXrefs chromosome map_location description 
    type_of_gene Symbol_from_nomenclature_authority Full_name_from_nomenclature_authority Nomenclature_status Other_designations Modification_date (tab is used as a separator, pound sign - start of a comment)
9606	1	A1BG	-	A1B|ABG|GAB|HYST2477	MIM:138670|HGNC:HGNC:5|Ensembl:ENSG00000121410|HPRD:00726|Vega:OTTHUMG00000183507	19	19q13.4	alpha-1-B glycoprotein	protein-coding	A1BG	alpha-1-B glycoprotein	O	HEL-S-163pA|alpha-1B-glycoprotein|epididymis secretory sperm binding protein Li 163pA	20150504
9606	2	A2M	-	A2MD|CPAMD5|FWP007|S863-7	MIM:103950|HGNC:HGNC:7|Ensembl:ENSG00000175899|HPRD:00072|Vega:OTTHUMG00000150267	12	12p13.31	alpha-2-macroglobulin	protein-coding	A2M	alpha-2-macroglobulin	O	C3 and PZP-like alpha-2-macroglobulin domain-containing protein 5|alpha-2-M	20150512
"""

    rdr = NCBITSVReader(StringIO(data))
    for rec in rdr:
        pprint(rec)
