import os,re,sys

import ometa.runtime

import hgvs.parser
import hgvs.variant
import hgvs.posedit
import hgvs.location

from uta.db.transcriptdb import TranscriptDB
from uta.exceptions import *
from uta.tools.transcriptmapper import TranscriptMapper
import uta.exceptions
import uta.utils.coords as uuc
import uta.utils.genomeutils as gu



dup_re = re.compile('(dup)\d+')

class HGVSMapper(object):

    def __init__(self,db=None,cache_transcripts=False):
        self.db = db
        self.cache_transcripts = cache_transcripts
        self.hgvs_parser = hgvs.parser.Parser()
        self.tm_cache = {}

    def fetch_TranscriptMapper(self,ac,ref='GRCh37.p10'):
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

        # InVitae: we use dupN, which is not part of the HGVS spec; remove number from dupN
        hgvs = dup_re.sub('\\1',hgvs)

        var = self.hgvs_parser.parse(hgvs)
        
        if var.seqref.startswith('NC_') and var.type == 'g':
            return (gu.NC_to_chr[var.seqref], var.posedit.pos.start, var.posedit.pos.end, None)
        
        if var.seqref.startswith('NM_') and var.type == 'c':
            tm = self.fetch_TranscriptMapper(var.seqref)
            c0 = uuc.cds_to_ci(var.posedit.pos.start.base, var.posedit.pos.end.base)
            g0 = tm.c_to_g(*c0)

            # Add intron offsets to genomic coordinates
            if tm.tx_info['strand'] == 1:
                g1_pos = (g0[0] + var.posedit.pos.start.offset+1, g0[1] + var.posedit.pos.end.offset  )
            else:
                g1_pos = (g0[0] - var.posedit.pos.end.offset+1,   g0[1] - var.posedit.pos.start.offset)

            return (tm.tx_info['chr'],g1_pos[0], g1_pos[1],tm)

        raise RuntimeError("Can't map {var.seqref}:{var.type} variants".format(var=var))


    def hgvsg_to_hgvsc(self,hgvs_g,ac,ref='GRCh37.p10'):
        """Given a genomic (g.) HGVS variant, return a transcript (c.) variant on the specified transcript.

        hgvs must be an HGVS-formatted variant or variant position.
        Certain InVitae variants are also permitted.
        """

        # InVitae: we use dupN, which is not part of the HGVS spec; strip N from dupN
        hgvs_g = dup_re.sub('\\1',hgvs_g)
        var_g = self.hgvs_parser.parse(hgvs_g)
        
        if not (var_g.seqref.startswith('NC_') and var_g.type == 'g'):
            raise InvalidHGVSVariantError('Expected a genomic (g.) variant on an NC sequence reference; got '+hgvs_g)

        chrom = gu.NC_to_chr[var_g.seqref]
        tm = self.fetch_TranscriptMapper(ac=ac,ref=ref)
        if not (chrom == tm.tx_info['chr']):
            raise InvalidTranscriptError('{hgvs_g} is on chromosome {chrom_g} but tried to map to transcript {ac} on chromosome {chrom_c}'.format(
                hgvs_g=hgvs_g, chrom_g=chrom, ac=ac, chrom_c=tm.tx_info['chr']))

        cse_i = tm.g_to_c( *uuc.human_to_ci(var_g.posedit.pos.start,var_g.posedit.pos.end) )
        cse_h = uuc.ci_to_human( *cse_i )
        
        # TODO: intronic offsets
        # TODO: revcomp edit for -strand
        var_c = hgvs.variant.Variant(seqref=ac,
                                     type='c',
                                     posedit=hgvs.posedit.PosEdit(
                                         pos=hgvs.location.Interval(
                                            start = hgvs.location.CDSPosition(base=cse_h[0],offset=0),
                                            end   = hgvs.location.CDSPosition(base=cse_h[1],offset=0)),
                                        edit=var_g.posedit.edit))
        return str(var_c)

        ## Add intron offsets
        #if tm.tx_info['strand'] == 1:
        #    g1_pos = (g0[0] + var.posedit.pos.start.offset+1, g0[1] + var.posedit.pos.end.offset  )
        #else:
        #    g1_pos = (g0[0] - var.posedit.pos.end.offset+1,   g0[1] - var.posedit.pos.start.offset)
