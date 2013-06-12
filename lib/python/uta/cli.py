from __future__ import absolute_import, division, print_function, unicode_literals

############################################################################

__doc__ = """UTA -- Universal Transcript Archive

Usage:
  uta ( -h | --help )
  uta --version
  uta [options] create-schema [ --drop-current ]
  uta [options] load-gene FILE
  uta [options] load-transcripts-gbff FILE
  uta [options] load-transcripts-seqgene FILE

Options:
  -C CONF, --conf CONF	Configuration to read (required)

"""

## Examples:
## All require
## export PYTHONPATH=lib/python
## 
## 1) Drop and create schema in PostgreSQL:
##   ./bin/uta -C etc/uta.conf create-schema --drop-current
## 
## 2) load data from seq_gene.md.gz files
##   ./bin/uta -C etc/uta.conf load-transcripts-seqgene misc/data/ftp.ncbi.nih.gov/genomes/MapView/Homo_sapiens/sequence/current/initial_release/seq_gene.md.gz
## 
## """

############################################################################

import csv, gzip, ConfigParser, itertools, logging

from Bio import SeqIO
from docopt import docopt
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import uta
import uta.models

############################################################################

def create_schema(engine,session,opts,cf):
    if opts['--drop-current']:
        session.execute('drop schema if exists '+uta.models.schema_name+' cascade')
        session.execute('create schema '+uta.models.schema_name)
        session.execute('alter database uta set search_path = '+uta.models.schema_name)

    session.commit()
    uta.models.Base.metadata.create_all(engine)
    session.add(uta.models.Meta(
            key='schema_version', value=uta.models.schema_version))
    session.commit()

############################################################################

def load_gene(engine,session,opts,cf):
    """
    import data as downloaded (by you) from 
    ftp://ftp.ncbi.nlm.nih.gov/gene/DATA/gene_info.gz
    """
    import uta.parsers.geneinfo
    gip = uta.parsers.geneinfo.GeneInfoParser(gzip.open(opts['FILE']))
    for gi in gip:
        if gi['tax_id'] != '9606' or gi['Symbol_from_nomenclature_authority'] == '-':
            continue
        g = uta.models.Gene(gene_id=gi['GeneID'], gene=gi['Symbol_from_nomenclature_authority'], 
                            name=gi['Full_name_from_nomenclature_authority'], maploc=gi['map_location'],
                            chrom=gi['chromosome'], descr=gi['description'])
        session.add(g)
        logging.info('loaded gene {g.gene} ({g.name})'.format(g=g))
    session.commit()

############################################################################

def load_transcripts_gbff(engine,session,opts,cf):
    """
    import data as downloaded (by you) from 
    ftp://ftp.ncbi.nlm.nih.gov/refseq/H_sapiens/mRNA_Prot/human.rna.gbff.gz
    """
    for rec in SeqIO.parse(gzip.open(opts['FILE']),'genbank'):
        if not rec.id.startswith('NM_'):
                continue
        #nseq_id = 
        #t = uta.models.Transcript(
        #    origin_id = 
        #    nseq_id =
        #    gene_id = 
        #    cds_start_i = STOPPED HERE
        #    )
        #import IPython; IPython.embed();
    
############################################################################

def load_transcripts_seqgene(engine,session,opts,cf):
    """
    import data as downloaded (by you) as from
    ftp.ncbi.nih.gov/genomes/MapView/Homo_sapiens/sequence/current/initial_release/seq_gene.md.gz
    """
    import uta.parsers.seqgene
    src = ( rec for rec in uta.parsers.seqgene.SeqGeneParser(gzip.open(opts['FILE']))
            if rec['transcript'].startswith('NM_') )
    for key,reciter in itertools.groupby(src, lambda r: r['transcript']):
        recs = list(reciter)
        import IPython; IPython.embed()
        

############################################################################

def run(argv=None):
    dispatch_table = [
        ('create-schema', 		create_schema),
        ('load-gene', 			load_gene),
        ('load-transcripts-gbff', 	load_transcripts_gbff),
        ('load-transcripts-seqgene', 	load_transcripts_seqgene),
        ]

    opts = docopt(__doc__, argv=argv, version=uta.__version__)

    logging.basicConfig(level=logging.INFO)

    cf = ConfigParser.SafeConfigParser()
    cf.readfp( open(opts['--conf']) )

    engine = create_engine(cf.get('uta','dsn')) #, echo=True)
    Session = sessionmaker(bind=engine) 
    session = Session()

    sub = None
    for cmd,func in dispatch_table:
        if opts[cmd]:
            sub = func
            break
    if sub is None:
        raise RuntimeError('No valid actions specified')
    sub(engine,session,opts,cf)
