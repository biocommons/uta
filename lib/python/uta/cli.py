#!/usr/bin/env python

from __future__ import absolute_import, division, print_function, unicode_literals

__doc__ = """UTA -- Universal Transcript Archive

Usage:
  uta ( -h | --help )
  uta --version
  uta -C CONF [options] create-schema
  uta -C CONF [options] load-gene eutils
  uta -C CONF [options] load-transcript gbff     --source=SOURCE
  uta -C CONF [options] load-transcript seqgene  --source=SOURCE

Global Options:
  --conf=CONF -C=CONF	Configuration to read (required)

Options:
  --source=SOURCE  	Source of data
"""

# eg$ /usr/bin/dropdb uta; /usr/bin/createdb -O reece uta; /usr/bin/psql -d uta -c 'create schema uta'; PYTHONPATH=lib/python ./bin/uta -C etc/uta.conf create-schema


############################################################################

from docopt import docopt
from ConfigParser import SafeConfigParser

import uta

############################################################################

def create_schema(opts,cf):
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    import uta.models

    engine = create_engine(cf.get('uta','dsn'), echo=True)
    Session = sessionmaker(bind=engine) 
    
    uta.models.Base.metadata.create_all(engine)
    
    # inject the schema version into the database
    session = Session()
    session.add(uta.models.Meta(
            key='schema_version', value=uta.models.schema_version))
    session.commit()

############################################################################

def run(argv=None):
    opts = docopt(__doc__, argv=argv, version=uta.__version__)

    cf = SafeConfigParser()
    cf.readfp( open(opts['--conf']) )

    dispatch_table = [
        ('create-schema', create_schema),
        ]

    for dte in dispatch_table:
        if opts[dte[0]]:
            dte[1](opts,cf)
            break
        raise RuntimeError('No valid actions specified')
