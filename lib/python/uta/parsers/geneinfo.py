import csv, io

from uta.exceptions import *

class GeneInfoParser(object):
    """Parse gene_info.gz files as from ftp://ftp.ncbi.nlm.nih.gov/gene/DATA/gene_info.gz"""
    def __init__(self,fh):
        self._fh = fh
        header = self._fh.next().rstrip()
        if header != '#Format: tax_id GeneID Symbol LocusTag Synonyms dbXrefs chromosome map_location description type_of_gene Symbol_from_nomenclature_authority Full_name_from_nomenclature_authority Nomenclature_status Other_designations Modification_date (tab is used as a separator, pound sign - start of a comment)':
            raise UTAError("""gene info doesn't contain expected header; got:\n{header}""".format(
                    header=header))
        fields = header.replace('#Format: ','').replace(' (tab is used as a separator, pound sign - start of a comment)','').split(' ')
        self._csvreader = csv.DictReader(self._fh, fieldnames = fields, delimiter = '\t')

    def __iter__(self):
        return self

    def next(self):
        return self._csvreader.next()
