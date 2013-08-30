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

