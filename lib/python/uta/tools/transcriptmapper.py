import re

from uta.tools.intervalmapper import IntervalMapper
from uta.exceptions import *

class TranscriptMapper(object):
    def __init__(self,db,ac,ref='GRCH37.p10'):
        self.db = db
        self.ref = ref
        self.ac = ac
        self.tx_info = db.get_tx_info(self.ac)
        self.tx_exons = db.get_tx_exons(self.ac,ref)
        if self.tx_info is None or len(self.tx_exons) == 0:
            raise UTAError("Couldn't build TranscriptMapper(ref={self.ref},ac={self.ac})".format(
                self=self))
        self.strand = self.tx_info['strand']
        self.cds_start_i = self.tx_info['cds_start_i']
        self.cds_end_i = self.tx_info['cds_end_i']
        self.gc_offset = self.tx_exons[0]['g_start_i']
        self.cigar = build_tx_cigar(self.tx_exons, self.strand)
        self.im = IntervalMapper.from_cigar(self.cigar)

    def __str__(self):
        return '{self.__class__.__name__}: {self.ac} ~ {self.ref}; {self.strand_pm} strand; {n_exons} exons; offset={self.gc_offset}'.format(
            self = self, n_exons = len(self.tx_exons))
    @property
    def strand_pm(self):
        return (None if self.strand is None
                else '+' if self.strand == 1
                else '-' if self.strand == -1
                else '?')

    def g_to_r(self,gs,ge):
        # frs, fre = forward cds start & end; forward meaning
        # w.r.t. genome and forward w.r.t. to + strand transcripts, or
        # backward w.r.t. to - strand transcripts
        frs,fre = self.im.map_ref_to_tgt(gs-self.gc_offset,ge-self.gc_offset)
        if self.strand == 1:
            return frs,fre
        elif self.strand == -1:
            return self.im.tgt_len-fre, self.im.tgt_len-frs
        else:
            raise UTAError("Code fell through strand check; shouldn't ever get here.")

    def r_to_g(self,rs,re):
        if self.strand == 1:
            frs, fre = rs, re
        elif self.strand == -1:
            frs, fre = self.im.tgt_len-re, self.im.tgt_len-rs
        else:
            raise UTAError("Code fell through strand check; shouldn't be here.")
        gs,ge = self.im.map_tgt_to_ref(frs,fre)
        return gs+self.gc_offset,ge+self.gc_offset

    def r_to_c(self,rs,re):
        return rs-self.cds_start_i, re-self.cds_start_i

    def c_to_r(self,cs,ce):
        return cs+self.cds_start_i, ce+self.cds_start_i

    def g_to_c(self,gs,ge):
        return self.r_to_c( *self.g_to_r(gs,ge) )
        
    def c_to_g(self,cs,ce):
        return self.r_to_g( *self.c_to_r(cs,ce) )


def build_tx_cigar(exons,strand):
    if len(exons) == 0:
        return None

    cigarelem_re = re.compile('\d+[DIMNX]')
    def _reverse_cigar(c):
        return ''.join(reversed(cigarelem_re.findall(c)))
    if strand == -1:
        for i in range(len(exons)):
            exons[i]['g_cigar'] = _reverse_cigar(exons[i]['g_cigar'])

    tx_cigar = [ exons[0]['g_cigar'] ]  # exon 1
    for i in range(1,len(exons)):     # and intron + exon pairs thereafter
        tx_cigar += [ str(exons[i]['g_start_i']-exons[i-1]['g_end_i']) + 'N',
                      exons[i]['g_cigar'] ]
    return ''.join(tx_cigar)


if __name__ == '__main__':
    ref = 'GRCh37.p10'
    ac = 'NM_182763.2'
    db = TranscriptDB()
    tm = TranscriptMapper(db,ac,ref)
