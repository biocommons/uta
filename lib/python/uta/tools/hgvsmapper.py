import os,re,sys

import ometa.runtime

from uta.db.transcriptdb import TranscriptDB

import uta.exceptions
from uta.tools.transcriptmapper import TranscriptMapper
import uta.utils.coords as uuc
import uta.utils.genomeutils as gu

import hgvs.parser

dup_re = re.compile('(dup)\d+')
ref = 'GRCh37.p10'

class HGVSMapper(object):

    def __init__(self,db=None,cache_transcripts=False):
        self.db = db
        self.cache_transcripts = cache_transcripts
        self.hgvs_parser = hgvs.parser.Parser()
        self.tm_cache = {}

    def fetch_TranscriptMapper(self,ac):
        """
        Get a new TranscriptMapper for the given transcript accession (ac),
        possibly caching the result.
        """
        try:
            tm = self.tm_cache[ac]
        except KeyError:
            tm = TranscriptMapper(self.db, ref = ref, ac = ac)
            if self.cache_transcripts:
                self.tm_cache[ac] = tm
        return tm
 
    def hgvs_to_genomic_coords(self,hgvs):
        """Returns (chr,start,end) for hgvs variant mapped to GRCh37 primary assembly.

        hgvs must be an HGVS-formatted variant or variant position.
        Certain InVitae variants are also permitted.

        chr is a GRCh37 chrosome with 'chr' prefix.
        start and end are 1-based, inclusive coordinates.
        """

        # remove number from dupN
        hgvs = dup_re.sub('\\1',hgvs)

        var = self.hgvs_parser.parse(hgvs)
        
        if var.seqref.startswith('NC_') and var.type == 'g':
            return (gu.NC_to_chr[var.seqref], var.pos.start, var.pos.end, None)
        
        if var.seqref.startswith('NM_') and var.type == 'c':
            tm = self.fetch_TranscriptMapper(var.seqref)
            c0 = uuc.cds_to_ci(var.pos.start.base, var.pos.end.base)
            g0 = tm.c_to_g(*c0)

            # Add intron offsets to genomic coordinates
            if tm.tx_info['strand'] == 1:
                g1_pos = (g0[0] + var.pos.start.offset+1, g0[1] + var.pos.end.offset  )
            else:
                g1_pos = (g0[0] - var.pos.end.offset+1,   g0[1] - var.pos.start.offset)

            return (tm.tx_info['chr'],g1_pos[0], g1_pos[1],tm)

        raise RuntimeError("Can't map {var.seqref}:{var.type} variants".format(var=var))
