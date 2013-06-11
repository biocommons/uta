import csv

from uta.exceptions import *

class SeqGeneParser(object):
    """parse mapping data as from ftp.ncbi.nih.gov/genomes/MapView/Homo_sapiens/sequence/current/initial_release/seq_gene.md.gz"""
    def __init__(self,fh):
        self._fh = fh
        header = self._fh.next().rstrip()
        if header != '#tax_id	chromosome	chr_start	chr_stop	chr_orient	contig	ctg_start	ctg_stop	ctg_orient	feature_name	feature_id	feature_type	group_label	transcript	evidence_code':
            raise UTAError("""file doesn't contain expected header; got:\n{header}""".format(
                    header=header))
        fields = header.replace('#','').split('\t')
        self._csvreader = csv.DictReader(self._fh, fieldnames = fields, delimiter = '\t')

    def __iter__(self):
        return self

    def next(self):
        return self._csvreader.next()


