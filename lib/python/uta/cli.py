from __future__ import absolute_import, division, print_function, unicode_literals

############################################################################

__doc__ = """UTA -- Universal Transcript Archive

Usage:
  uta ( -h | --help )
  uta --version
  uta [options] create-schema [--drop-current]
  uta [options] load-gene FILE
  uta [options] load-transcripts-gbff FILE
  uta [options] load-transcripts-seqgene FILE

Options:
  -C CONF, --conf CONF	Configuration to read (required)


Examples:

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

import ConfigParser, logging

#from Bio import SeqIO
from docopt import docopt
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import uta
import uta.db.loading as ul

def run(argv=None):
    dispatch_table = [
        ('create-schema', 		ul.create_schema),
        ('load-gene', 			ul.load_gene),
        ('load-transcripts-gbff', 	ul.load_transcripts_gbff),
        ('load-transcripts-seqgene', 	ul.load_transcripts_seqgene),
        ]

    opts = docopt(__doc__, argv=argv, version=uta.version.hg_id)

    logging.basicConfig(level=logging.INFO)

    cf = ConfigParser.SafeConfigParser()
    cf.readfp( open(opts['--conf']) )

    engine = create_engine(cf.get('uta','db_url_loading')) #, echo=True)
    Session = sessionmaker(bind=engine) 
    session = Session()

    sub = None
    for cmd,func in dispatch_table:
        if opts[cmd]:
            sub = func
            break
    if sub is None:
        raise UTAError('No valid actions specified')
    sub(engine,session,opts,cf)
