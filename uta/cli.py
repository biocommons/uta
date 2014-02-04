from __future__ import absolute_import, division, print_function, unicode_literals

############################################################################

__doc__ = """uta -- Universal Transcript Archive command line tool

Usage:
  uta ( -h | --help )
  uta --version
  uta [options] shell
  uta [options] drop-schema
  uta [options] create-schema
  uta [options] create-views FILES ...
  uta [options] initialize-schema
  uta [options] rebuild
  uta [options] load-seqinfo FILE
  uta [options] load-geneinfo FILE
  uta [options] load-txinfo FILE
  uta [options] load-exonsets FILE
  uta [options] align-exons FASTA_DIR
  uta [options] load-ncbi-seqgene FILE
  
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

import ConfigParser
import logging
import time

import docopt

import uta
import uta.loading as ul
usam = uta.models                         # backward compatibility


def shell(session,opts,cf):
    import IPython; IPython.embed()

def rebuild(*args):
    ul.drop_schema(*args)
    ul.create_schema(*args)
    ul.initialize_schema(*args)

def run(argv=None):
    dispatch_table = [
        ('drop-schema',                 ul.drop_schema),
        ('create-schema',               ul.create_schema),
        ('create-views',                ul.create_views),
        ('initialize-schema',           ul.initialize_schema),
        ('rebuild',                     rebuild),

        ('load-exonsets',               ul.load_exonsets),
        ('load-geneinfo',               ul.load_geneinfo),
        ('load-seqinfo',                ul.load_seqinfo),
        ('load-txinfo',                 ul.load_txinfo),

        ('align-exons',					ul.align_exons),

        ('load-ncbi-seqgene',           ul.load_ncbi_seqgene),

        ('shell',                       shell),
        ]

    opts = docopt.docopt(__doc__, argv=argv, version=uta.__version__)

    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)

    cf = ConfigParser.SafeConfigParser()
    cf.readfp( open(opts['--conf']) )
    db_url = cf.get('uta','db_loading_url')
    session = uta.connect(db_url)

    sub = None
    for cmd,func in dispatch_table:
        if opts[cmd]:
            sub = func
            break
    if sub is None:
        raise UTAError('No valid actions specified')
    t0 = time.time()
    sub(session,opts,cf)
    logger.info("{cmd}: {elapsed:.1f}s elapsed".format(cmd=cmd,elapsed=time.time()-t0))


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
