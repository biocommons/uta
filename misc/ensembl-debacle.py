# investigate cases where one ENST is associated with multiple
# sequences (not indentical)

import hashlib
import itertools
import os
import pprint

from multifastadb import MultiFastaDB
from prettytable import PrettyTable
import uta_align.align.algorithms as utaaa


_seq_md5s = dict()
def seq_md5(s):
    """cached seq -> md5 hex hash"""
    h = hashlib.md5(s).hexdigest()
    _seq_md5s[h] = s
    return h

def build_ac_hash_map(mfdb):
    return {ac: seq_md5(str(mfdb[ac]).upper()) for ac in mfdb.references}

def build_hash_acs_map(ahm):
    ha_pairs = sorted((h, ac) for ac, h in ahm.iteritems())
    ha_map = {h: sorted(list(e[1] for e in hai))
              for h, hai in itertools.groupby(ha_pairs, key=lambda ha: ha[0])}
    return ha_map 

def build_wac_map(mfdb):
    """return {ac: {md5: [faf]}}"""
    for ac in mfdb.references:
        ffs = [loc[1] for loc in mfdb.where_is(ac)]
        for ff in ffs:
            md5 = seq_md5(ff[ac])
            

    return {ac: (ff,) 

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
            'md5': seq_md5(seq),
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

def multiplicity2(mfdb, acs, all=False):
    acw = {ac: mfdb.where_is(ac) for ac in acs}
    if not all:
        acw = {ac: w for ac, w in acw.iteritems() if len(w)>1}

    return {
        ac: [hashlib.md5(s).hexdigest()
             for s in set(str(w[1]).upper() )]
        for ac, w in acw.iteritems()
        } 




if __name__ == "__main__":
    path = '/local/home/reece/data/ftp.ensembl.org/pub/'
    all = sorted([os.path.join(dir, f)
                  for dir, _, files in os.walk(path)
                  for f in files if f.endswith('.fa.bgz') and 'abinitio' not in f])

    grch37 = [f for f in all if '.GRCh37.' in f]
    grch38 = [f for f in all if '.GRCh38.' in f]
    pep = [f for f in all if '/pep/' in f]
    ncrna = [f for f in all if '/ncrna/' in f]
    cds = [f for f in all if '/cds/' in f]
    cdna = [f for f in all if '/cdna/' in f]
    v = {v: [f for f in all if 'release-' + v in f] for v in "70 71 72 73 74 75 79 81".split()}

    sources = v['79']
    mfdb = MultiFastaDB(sources=sources)

    ham = build_ac_hash_map(mfdb)
    ahm = build_hash_acs_map(ham)
    
