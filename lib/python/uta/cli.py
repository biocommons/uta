from __future__ import absolute_import, division, print_function, unicode_literals

############################################################################

__doc__ = """UTA -- Universal Transcript Archive

Usage:
  uta ( -h | --help )
  uta --version
  uta [options] create-schema [--drop-current]
  uta [options] load-eutils-by-gene GENES ...
  uta [options] load-gene-info FILE
  uta [options] load-transcripts-gbff FILE
  uta [options] load-transcripts-seqgene FILE

Options:

  -C CONF, --conf CONF	Configuration to read (required)


Examples:

  $ ./bin/uta --conf etc/uta.conf create-schema --drop-current

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
        ('create-schema',               ul.create_schema),
        ('load-eutils-by-gene',         ul.load_eutils_by_gene),
        ('load-gene-info',              ul.load_gene_info),
        ('load-transcripts-gbff',       ul.load_transcripts_gbff),
        ('load-transcripts-seqgene',    ul.load_transcripts_seqgene),
        ]

    opts = docopt(__doc__, argv=argv, version=uta.__version__)

    logging.basicConfig(level=logging.INFO)

    cf = ConfigParser.SafeConfigParser()
    cf.readfp( open(opts['--conf']) )

    engine = create_engine(cf.get('uta','db_loading_url')) #, echo=True)
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


## <LICENSE>
## Copyright 2014 UTA Contributors (https://bitbucket.org/invitae/uta)
## 
## Licensed under the Apache License, Version 2.0 (the "License");
## you may not use this file except in compliance with the License.
## You may obtain a copy of the License at
## 
##     http://www.apache.org/licenses/LICENSE-2.0
## 
## Unless required by applicable law or agreed to in writing, software
## distributed under the License is distributed on an "AS IS" BASIS,
## WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
## See the License for the specific language governing permissions and
## limitations under the License.
## </LICENSE>
