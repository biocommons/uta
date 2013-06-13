import csv, itertools

from uta.exceptions import *

class SeqGeneParser(object):
    """parse mapping data as from ftp.ncbi.nih.gov/genomes/MapView/Homo_sapiens/sequence/current/initial_release/seq_gene.md.gz"""
    def __init__(self,fh,filter=None):
        self._fh = fh
        self._filter = filter if filter else lambda r: True
        header = self._fh.next().rstrip()
        if header != '#tax_id	chromosome	chr_start	chr_stop	chr_orient	contig	ctg_start	ctg_stop	ctg_orient	feature_name	feature_id	feature_type	group_label	transcript	evidence_code':
            raise UTAError("""file doesn't contain expected header; got:\n{header}""".format(
                    header=header))
        fields = header.replace('#','').split('\t')
        self._csvreader = csv.DictReader(self._fh, fieldnames = fields, delimiter = '\t')

    def __iter__(self):
        return self

    def next(self):
        for r in self._csvreader:
            if self._filter(r):
                return r
        raise StopIteration


## The following code doesn't work and I don't know why.
## class SeqGeneBlockParser(object):
##     """parse mapping data as from ftp.ncbi.nih.gov/genomes/MapView/Homo_sapiens/sequence/current/initial_release/seq_gene.md.gz"""
##     def __init__(self,fh,filter=None):
##         self._sgparser = SeqGeneParser(fh,filter)
## 
##     def __iter__(self):
##         return self
## 
##     def next(self):
##         slurp = list(self._sgparser)
##         slurp.sort(key = lambda r: (r['transcript'],r['group_label'],r['chr_start'],r['chr_stop']))
##         iter = itertools.groupby(slurp, key = lambda r: (r['transcript'],r['group_label']))
##         import IPython; IPython.embed()
##         for k,i in iter:
##             return k,i
##         raise StopIteration


if __name__ == '__main__':
    import gzip, prettytable, IPython, sys
    fh = gzip.open(sys.argv[1])
    nm_filter = lambda r: r['transcript'].startswith('NM_')
    sgparser = SeqGeneParser(fh,filter = nm_filter)
    slurp = list(sgparser)
    slurp.sort(key = lambda r: (r['transcript'],r['group_label'],r['chr_start'],r['chr_stop']))
    iter = itertools.groupby(slurp, key = lambda r: (r['transcript'],r['group_label']))
    for k,i in iter:
        print(k,len(list(i)))
