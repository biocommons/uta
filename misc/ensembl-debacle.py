# investigate cases where one ENST is associated with multiple
# sequences (not indentical)

import hashlib
import itertools
import pprint
from multifastadb import MultiFastaDB; import uta_align.align.algorithms as utaaa
from prettytable import PrettyTable

path = '/local/home/reece/data/ftp.ensembl.org/pub/'

try:
    _ = mfdb
except NameError:
    mfdb = MultiFastaDB(sources=[path])

hashed_seqs = dict()
def hashseq(s):
    h = hashlib.md5(s).hexdigest()
    hashed_seqs[h] = s
    return h

def summary(ac):
    def _srec(s):
        seq = s[1][ac]
        rpath = s[0].replace(path, '')
        rpathc = rpath.split('/')
        rls = rpathc[0]
        type_ = 'cds' if 'cds' in rpathc[-1] else 'cdna' if 'cdna' in rpathc[-1] else '?'
        assy = 'GRCh37' if 'GRCh37' in rpathc[-1] else 'GRCh38' if 'GRCh38' in rpathc[-1] else '?'
        return {
            'assy': assy,
            'faf': s[1],
            'len': len(seq),
            'md5': hashseq(seq),
            'rls': rls,
            'rpath': rpath,
            'type': type_,
            }
    return [_srec(s) for s in mfdb.where_is(ac)]

def binned_summary(ac):
    return { k:list(v) for k,v in itertools.groupby(sorted(summary(ac), key=lambda e: e['md5']), key=lambda e: e['md5']) }

def table_summary(ac):
    cols = ['len','md5','rls','assy','type']
    def _sorter(e):
        return tuple(e[c] for c in cols)
    pt = PrettyTable(field_names=cols)
    for row in sorted(summary(ac), key=_sorter):
        pt.add_row([str(row[c]) for c in cols])
    return pt

def align(s1, s2):
    return utaaa.align(str(s1), str(s2), mode='glocal', extended_cigar=True)

def multiplicity(acs):
    return {ac:[hashlib.md5(s).hexdigest() for s in set(str(w[1][ac]).upper() for w in mfdb.where_is(ac))] for ac in acs} 

