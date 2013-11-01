import re
import math

from uta.tools.intervalmapper import IntervalMapper
from uta.exceptions import *

# TODO: use ci_to_cds/cds_to_ci

class TranscriptMapper(object):
    __doc__ = """
    All coordinates are interbase (0-based, right-open)

    gs, ge = genomic start,end
    rs, re = rna start,end
    cs, ce = cds start,end

    NOTE: cs and ce are continuous coordinates, unlike the HGVS CDS coordinate
    which have no 0 (i.e., ..,-2,-1,1,2,..).  See uta.utils.coords for interval
    and coordinate conversion functions.
    """

    def __init__(self, db, ac, ref='GRCH37.p10'):
        self.db = db
        self.ref = ref
        self.ac = ac
        self.tx_info = db.get_tx_info(self.ac)
        self.tx_exons = db.get_tx_exons(self.ac, ref)
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
            self=self, n_exons=len(self.tx_exons))

    @property
    def strand_pm(self):
        return (None if self.strand is None
                else '+' if self.strand == 1
        else '-' if self.strand == -1
        else '?')

    def g_to_r(self, gs, ge):
        # frs, fre = (f)orward (r)na (s)tart & (e)nd; forward w.r.t. genome
        frs, fre = self.im.map_ref_to_tgt(gs - self.gc_offset, ge - self.gc_offset, max_extent=False)
        if self.strand == 1:
            frs, fre = frs, fre
        elif self.strand == -1:
            frs, fre = self.im.tgt_len - fre, self.im.tgt_len - frs
        else:
            raise UTAError("Code fell through strand check; shouldn't ever get here.")

        # check for 0-width mapping indicating the gs and ge were in an intron and we need the offsets
        if (fre - frs) == 0:
            # returns the genomic range start (grs) and end (gre)
            # this range could be an intron bounds or just a genomic range
            grs, gre = self.r_to_g(frs, fre, 0, 0)
            rso, reo = self.intronic_offsets(gs, ge, grs, gre)
            if self.strand == -1:
                rso, reo = self.strand * reo, self.strand * rso
        else:
            rso = 0
            reo = 0

        return frs, fre, rso, reo

    def r_to_g(self, rs, re, rso=0, reo=0):
        if self.strand == 1:
            frs, fre = rs, re
        elif self.strand == -1:
            frs, fre = self.im.tgt_len - re, self.im.tgt_len - rs
            rso, reo = self.strand * reo, self.strand * rso
        else:
            raise UTAError("Code fell through strand check; shouldn't be here.")

        # returns the genomic range start (grs) and end (gre)
        grs, gre = self.im.map_tgt_to_ref(frs, fre, max_extent=False)
        grs, gre = grs + self.gc_offset, gre + self.gc_offset

        if rso == 0 and reo == 0:   # no offset
            gs, ge = grs, gre
        elif rso >= 0 and reo > 0:  # positive offset
            gs = grs + rso
            ge = grs + reo
        elif rso < 0 and reo <= 0:  # negative offset
            gs = gre + rso
            ge = gre + reo
        else:                       # positive and negative offset
            gs = grs + rso
            ge = gre + reo

        return gs, ge

    def r_to_c(self, rs, re, rso=0, reo=0):
        return rs - self.cds_start_i, re - self.cds_start_i, rso, reo

    def c_to_r(self, cs, ce, cso=0, ceo=0):
        return cs + self.cds_start_i, ce + self.cds_start_i, cso, ceo

    def g_to_c(self, gs, ge):
        cs, ce, cso, cse = self.r_to_c(*self.g_to_r(gs, ge))
        return cs, ce, cso, cse

    def c_to_g(self, cs, ce, cso=0, cse=0):
        gs, ge = self.r_to_g(*self.c_to_r(cs, ce, cso, cse))
        return gs, ge

    def _debug_info(self):
        import prettytable, textwrap

        ti_table = prettytable.PrettyTable(field_names=['k', 'v'])
        ti_table.align['k'] = 'r'
        ti_table.align['v'] = 'l'
        fields = ['ac', 'gene', 'descr', 'strand', 'cds_start_i', 'cds_end_i', 'summary', ]
        for f in fields:
            ti_table.add_row([f, textwrap.fill(str(self.tx_info[f]), 80)])

        fields = ['ref', 'ac', 'ord', 'name', 't_start_i', 't_end_i', 'g_start_i', 'g_end_i', 'g_cigar']
        ex_table = prettytable.PrettyTable(field_names=fields)
        for ex in sorted(self.tx_exons, key=lambda ex: ex['ord']):
            ex_table.add_row([ex[f] for f in fields])

        return str(ti_table) + "\n" + str(ex_table)

    def intronic_offsets(self, gs, ge, grs, gre):
        """ Calculates intron offsets for a set of genomic start (gs) and end (ge)

        Here's how we handle the mid point between exons...

        1_2_3_4_5_6
         A C T G C
        mid = 3.5 or T, so we round up call it 4. Everyone wants more positive things

        1_2_3_4_5_6_7
         A C T G C A
        mid = 4 - no problem.  (4,5) = -G or (3,4) = +T
        """
        mid = math.ceil((grs + gre) / 2)

        # left +
        if gs < mid and ge <= mid:
            gso = gs - grs
            geo = ge - grs

        # right -
        elif gs >= mid and ge > mid:
            gso = gs - gre
            geo = ge - gre

        # span +/-
        else:
            gso = gs - grs
            geo = ge - gre

        return gso, geo

def build_tx_cigar(exons, strand):
    if len(exons) == 0:
        return None

    cigarelem_re = re.compile('\d+[DIMNX]')

    def _reverse_cigar(c):
        return ''.join(reversed(cigarelem_re.findall(c)))

    if strand == -1:
        for i in range(len(exons)):
            exons[i]['g_cigar'] = _reverse_cigar(exons[i]['g_cigar'])

    tx_cigar = [exons[0]['g_cigar']]  # exon 1
    for i in range(1, len(exons)):     # and intron + exon pairs thereafter
        tx_cigar += [str(exons[i]['g_start_i'] - exons[i - 1]['g_end_i']) + 'N',
                     exons[i]['g_cigar']]
    return ''.join(tx_cigar)


if __name__ == '__main__':
    from uta.db.transcriptdb import TranscriptDB

    ref = 'GRCh37.p10'
    ac = 'NM_145249.2'
    db = TranscriptDB()
    tm = TranscriptMapper(db,ac,ref)
