import re

from uta.exceptions import *

class Interval(object):
    __slots__ = ('start_i','end_i')
    def __init__(self,start_i,end_i):
        self.start_i = start_i
        self.end_i = end_i
        if not self.start_i <= self.end_i:
            raise InvalidIntervalError('start_i must be less than or equal to end_i')
    @property
    def len(self):
        return self.end_i - self.start_i
    def __repr__(self):
        return str(self)
    def __str__(self):
        return '{self.__class__.__name__}(start_i={self.start_i},end_i={self.end_i})'.format(self=self)


class IntervalPair(object):
    __slots__ = ('ref','tgt')
    def __init__(self,ref,tgt):
        self.ref = ref
        self.tgt = tgt
        # TODO: check for overlapping
        # TODO: check for ordering
        # TODO: check for adjacency
        # TODO: new class for ungapped (lengths == ?)
        if self.ref.len != self.tgt.len and self.ref.len != 0 and self.tgt.len != 0:
            raise InvalidIntervalError('intervals must have equal lengths (|{self.ref}| != |{self.tgt}|)'.format(
                self=self))
    def __repr__(self):
        return str(self)
    def __str__(self):
        return '{self.__class__.__name__}(ref={self.ref},tgt={self.tgt})'.format(self=self)


class IntervalMapper(object):
    __slots__ = ('interval_pairs','ref_intervals','tgt_intervals','ref_len','tgt_len')
    def __init__(self,interval_pairs):
        self.interval_pairs = interval_pairs
        self.ref_intervals = [ ip.ref for ip in self.interval_pairs ]
        self.tgt_intervals = [ ip.tgt for ip in self.interval_pairs ]
        self.ref_len = sum([ iv.len for iv in self.ref_intervals ])
        self.tgt_len = sum([ iv.len for iv in self.tgt_intervals ])

    @staticmethod
    def from_cigar(cigar):
        return IntervalMapper(cigar_to_intervalpairs(cigar))

    def map_ref_to_tgt(self,start_i,end_i):
        return self._map(self.ref_intervals, self.tgt_intervals, start_i, end_i)

    def map_tgt_to_ref(self,start_i,end_i):
        return self._map(self.tgt_intervals, self.ref_intervals, start_i, end_i)

    @staticmethod
    def _map(from_ivs,to_ivs,from_start_i,from_end_i):
        # x_index_ext functions return the *maximal* span of an interval,
        # extending across adjacent insertions.  This is nice in some
        # circumstances, but violates principle of least surprise. 
        def s_index_ext(ivs,s):
            return min([ i for i,iv in enumerate(ivs) if iv.start_i <= s <  iv.end_i or iv.end_i   == s])
        def e_index_ext(ivs,e):
            return max([ i for i,iv in enumerate(ivs) if iv.start_i <  e <= iv.end_i or iv.start_i == e])
        def s_index(ivs,s):
            return max([ i for i,iv in enumerate(ivs) if iv.start_i <= s ])
        def e_index(ivs,e):
            return min([ i for i,iv in enumerate(ivs[si:]) if e <= iv.end_i ]) + si
        def clip_to_iv(iv,pos):
            return max(iv.start_i,min(iv.end_i,pos))
        assert from_start_i != 0 and from_end_i != 0 and from_start_i<=from_end_i, 'expected from_start_i <= from_end_i'
        try:
            si = s_index(from_ivs,from_start_i)
            ei = e_index(from_ivs,from_end_i)
        except ValueError:
            raise InvalidIntervalError('start_i,end_i interval out of bounds')
        to_start_i = clip_to_iv( to_ivs[si], to_ivs[si].start_i + (from_start_i - from_ivs[si].start_i) )
        to_end_i   = clip_to_iv( to_ivs[ei], to_ivs[ei].end_i   - (from_ivs[ei].end_i - from_end_i)     )
        #print('from se: (%d,%d); selected si=%d, ei=%d, to se: (%d,%d), from_ivs:\n%s' % (
        #    from_start_i,from_end_i,si,ei,to_start_i,to_end_i,str(from_ivs)))
        return to_start_i,to_end_i


class CIGARElement(object):
    __slots__ = ('len','op')
    def __init__(self,len,op):
        self.len = len
        self.op = op
    @property
    def ref_len(self):
        """returns number of nt/aa consumed in reference sequence for this edit"""
        return self.len if self.op in 'DMNX' else 0
    @property
    def tgt_len(self):
        """returns number of nt/aa consumed in target sequence for this edit"""
        return self.len if self.op in 'IMX'  else 0

def cigar_to_intervalpairs(cigar):
    cigar_elem_re = re.compile('(?P<len>\d+)(?P<op>[DIMNX])')
    ces = [ CIGARElement(op=md['op'],len=int(md['len']))
            for md in [ m.groupdict() for m in cigar_elem_re.finditer(cigar) ] ]
    ips = [None] * len(ces)
    ref_pos = tgt_pos = 0
    for i,ce in enumerate(ces):
        ips[i] = IntervalPair( Interval(ref_pos,ref_pos+ce.ref_len),
                               Interval(tgt_pos,tgt_pos+ce.tgt_len) )
        ref_pos += ce.ref_len
        tgt_pos += ce.tgt_len
    return ips


if __name__ == '__main__':
    # Tests the following alignment:
    # 0                   20            35         45       55
    # |===================|==============|---------|=========|
    # |                   |\__            \___ ___/       __/
    # |                   |   \               v          /
    # |===================|----|==============|=========|
    # 0                  20   25             40        50
    # 
    # generated from:
    # print( cigar_to_intervalpairs('20M5I15M10D10M') )
    im = IntervalMapper([
        IntervalPair(ref=Interval(start_i= 0,end_i=20),tgt=Interval(start_i= 0,end_i=20)),
        IntervalPair(ref=Interval(start_i=20,end_i=20),tgt=Interval(start_i=20,end_i=25)),
        IntervalPair(ref=Interval(start_i=20,end_i=35),tgt=Interval(start_i=25,end_i=40)),
        IntervalPair(ref=Interval(start_i=35,end_i=45),tgt=Interval(start_i=40,end_i=40)),
        IntervalPair(ref=Interval(start_i=45,end_i=55),tgt=Interval(start_i=40,end_i=50)),
        ])
