===================================
UTA -- Universal Transcript Archive
===================================

*bringing smiles to transcript users since 2013*


Overview
--------

The UTA stores transcripts aligned to genome reference assemblies using
multiple methods in order to improve the precision and accuracy by which
the scientific and clinical communities describe variants.

It will facilitate the following:

* enabling an interpretation of variants reported in literature against
  obsolete transcript records
* identifying regions where transcript and reference genome sequence
  assemblies disagree
* characterizing transcripts of the same gene across transcript sources
* projecting ("lifting over") variants from one transcript to another
* identifying transcripts and genomic regions with ambiguous alignments
  that may affect clinical interpretation
* querying for multiple transcript sources through a single
  interface



Examples
--------
The code is still in tremendous flux.  The API is evolving.  With that
said, the following does work::

  snafu$ mkvirtualenv hgvsmapping
  New python executable in hgvsmapping/bin/python
  ... 

  (hgvsmapping)snafu$ pip install hg+ssh://hg@bitbucket.org/locusdevelopment/uta
  (hgvsmapping)snafu$ ipython

  In [1]: from uta.db.transcriptdb import TranscriptDB

  In [2]: from uta.tools.hgvsmapper import HGVSMapper
  
  In [3]: hgvsmapper = HGVSMapper(db = TranscriptDB(), cache_transcripts=True)
  
  # When called with an NC, hgvs_to_genomic_coords parses the HGVS string, translates
  # the NC to a chromosome, and returns the whole thing.
  In [4]: hgvsmapper.hgvs_to_genomic_coords('NC_000007.13:g.36561662C>T')
  Out[4]: ('7', 36561662, 36561662, None)
  
  # When called with an NM, maps the variant to genomic coords. This is on the - strand, so 
  # the alleles are complemented
  In [5]: hgvsmapper.hgvs_to_genomic_coords('NM_001177507.1:c.1486G>A')
  Out[5]: 
  ('7',
   36561662,
   36561662,
   <uta.tools.transcriptmapper.TranscriptMapper at 0x2db4b10>)
  
  # capture the results. tm is the TranscriptMapper, which contains references to transcript, gene, and exon info.
  In [6]: chrom,start,end,tm = hgvsmapper.hgvs_to_genomic_coords('NM_001177507.1:c.1486G>A')

  In [7]: tm.tx_info
  Out[7]: 
  ['AOAH',
   '7',
   -1,
   'NM_001177507.1',
   401,
   2033,
   'acyloxyacyl hydrolase (neutrophil)',
   'This locus encodes both the light and heavy subunits of acyloxyacyl hydrolase. The encoded enzyme catalyzes the hydrolysis of acyloxylacyl-linked fatty acyl chains from bacterial lipopolysaccharides, effectively detoxifying these molecules. The encoded protein may play a role in modulating host inflammatory response to gram-negative bacteria. Alternatively spliced transcript variants have been described.[provided by RefSeq, Apr 2010]']

  # exons, in genome order (this is on the minus strand, so they come in reverse order of the transcript)
  In [8]: tm.tx_exons
  Out[8]: 
  [['NM_001177507.1',
    20,
    '22',
    1904,
    2344,
    'GRCh37.p10',
    36552548,
    36552986,
    '184M1I60M1I194M',
    'GTGGCTTTGCTGTTGTTGGCGGATCATTTCTGGAAAAAGGTGCAGCTCCAGTGGCCCCAAATCCTGGGAAAGGAGAATCCGTTCAACCCCCAGATTAAACAGGTGTTTGGAGACCAAGGCGGGCACTGAGCCTCTCAGGAGCATGCACCCCTGGGGAGCACAGGGAGGCAGAGGCTTGGGTAAACTCATTCCAC-AACCCTATGGGGGCTGCCACGTCACAGGCCCAAAGGACTCTTCTTCAGCAGCATCTTTGC-AAATGTCTTTCTCTCAATGAAGAGCATATCTGGACGACTGTGCAATGCTGTGTGCTCCCGGGATCAGTAACCCTTCCGCTGTTCCTGAAATAACCTTTCATAAAGTGCTTTGGGTGCCATTCCAAACAAGAGAGTATCTGTGCCCTTTACAGCTAATTGTTCTAAAAGGAGTTTCTAAAAACAC',
    'GTGGCTTTGCTGTTGTTGGCGGATCATTTCTGGAAAAAGGTGCAGCTCCAGTGGCCCCAAATCCTGGGAAAGGAGAATCCGTTCAACCCCCAGATTAAACAGGTGTTTGGAGACCAAGGCGGGCACTGAGCCTCTCAGGAGCATGCACCCCTGGGGAGCACAGGGAGGCAGAGGCTTGGGTAAACTCATTCCACAAACCCTATGGGGGCTGCCACGTCACAGGCCCAAAGGACTCTTCTTCAGCAGCATCTTTGCAAAATGTCTTTCTCTCAATGAAGAGCATATCTGGACGACTGTGCAATGCTGTGTGCTCCCGGGATCAGTAACCCTTCCGCTGTTCCTGAAATAACCTTTCATAAAGTGCTTTGGGTGCCATTCCAAACAAGAGAGTATCTGTGCCCTTTACAGCTAATTGTTCTAAAAGGAGTTTCTAAAAACAC'],
   ['NM_001177507.1',
    19,
    '20',
   ...

Older Instructions::

  from uta.db.transcriptdb import TranscriptDB
  from uta.exceptions import *
  from uta.tools.transcriptmapper import TranscriptMapper
  import hgvs.parser
  
  ref = 'GRCh37.p10'
  hgvs_c = 'NM_144588.6:c.805-15_805-11del5'
  
  
  # Connect to the UTA database (AWS VPC, PostgreSQL)
  db = TranscriptDB()
  
  # Create a parser instance
  # [This is a PEG-based parser with relatively complete support
  # for single (non-compound) genomic and cDNA variants.]
  hgvs_parser = hgvs.parser.Parser()
  
  var_c = hgvs_parser.parse(hgvs_c)
  
  # A transcript mapper object
  tm = TranscriptMapper(db, ref = ref, ac = var_c.seqref)
  
  # For the moment, TranscriptMapper knows nothing of HGVS structures,
  # so you have to hand it raw coordinates
  # IMPORTANT: UTA always uses interbase coordinates (0-based, right-open)
  c0 = (var_c.pos.start.base - 1, var_c.pos.end.base)
  g0 = tm.c_to_g(*c0)
  
  # Add IVS offsets to genomic coordinates
  # N.B. This works for + strand only; need to swap var_c start/end for - strand
  g_pos = (g0[0] + var_c.pos.start.offset, g0[1] + var_c.pos.end.offset)

