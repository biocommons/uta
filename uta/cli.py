from __future__ import absolute_import, division, print_function, unicode_literals

############################################################################

__doc__ = """uta -- Universal Transcript Archive command line tool

Usage:
  uta ( -h | --help )
  uta --version
  uta (-C CONF ...) [options] shell
  uta (-C CONF ...) [options] drop-schema
  uta (-C CONF ...) [options] create-schema
  uta (-C CONF ...) [options] load-sql FILES ...
  uta (-C CONF ...) [options] initialize-schema
  uta (-C CONF ...) [options] rebuild
  uta (-C CONF ...) [options] load-seqinfo FILE
  uta (-C CONF ...) [options] load-geneinfo FILE
  uta (-C CONF ...) [options] load-txinfo FILE
  uta (-C CONF ...) [options] load-exonsets FILE
  uta (-C CONF ...) [options] load-sequences
  uta (-C CONF ...) [options] align-exons [--sql SQL]
  uta (-C CONF ...) [options] load-ncbi-seqgene FILE
  uta (-C CONF ...) [options] grant-permissions
  
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
    ul.grant_permissions(*args)

def run(argv=None):
    dispatch_table = [
        ('drop-schema',                 ul.drop_schema),
        ('create-schema',               ul.create_schema),
        ('initialize-schema',           ul.initialize_schema),
        ('grant-permissions',           ul.grant_permissions),
        ('rebuild',                     rebuild),

        ('load-sql', 	                ul.load_sql),

        ('load-exonsets',               ul.load_exonsets),
        ('load-geneinfo',               ul.load_geneinfo),
        ('load-seqinfo',                ul.load_seqinfo),
        ('load-txinfo',                 ul.load_txinfo),
        ('load-sequences',              ul.load_sequences),

        ('align-exons',					ul.align_exons),

        ('load-ncbi-seqgene',           ul.load_ncbi_seqgene),

        ('shell',                       shell),
        ]

    opts = docopt.docopt(__doc__, argv=argv, version=uta.__version__)

    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)

    # cf_loaded: deal with docopt issue https://github.com/docopt/docopt/issues/134
    cf = ConfigParser.SafeConfigParser()
    cf_loaded = dict()
    for conf_fn in opts['--conf']:
        if conf_fn not in cf_loaded:
            cf.readfp( open(conf_fn) )
            cf_loaded[conf_fn] = True
            logger.info('loaded '+conf_fn)

    db_url = cf.get('uta','db_url')
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
## Copyright 2014 UTA Contributors (https://bitbucket.org/biocommons/uta)
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
