"""
The "transcripts" DB contains transcripts from NCBI with alignments to
GRCh37 (the reference genome.)  This module provides a simple API to the
database.

Eventually, this transcripts database will be replaced by a dedicated UTA
database that offers more extensive transcript data, including archived
transcripts, alternate assemblies and multiple alignment methods.  We will
attempt to preserve this API.


Example
.......

    # >>> from uta.db.transcriptdb import TranscriptDB
    # >>> db = TranscriptDB()
    # >>> tx_info = db.get_tx_info('NM_000051.3')
    # >>> tx_info['gene']
    # 'ATM'
"""

import logging
import os
import sys

import psycopg2
import psycopg2.extras
from psycopg2 import OperationalError


if 'UTA_DB_URL' in os.environ:
    # Use UTA_DB_URL for connection information, if available
    # Examples:
    # UTA_DB_URL=postgresql://uta_public:uta_public@uta.invitae.com/uta -- same as default
    # UTA_DB_URL=postgresql://localhost/uta                             -- localhost via socket, as user, database=username:
    import urlparse
    url = urlparse.urlparse(os.environ['UTA_DB_URL'])
    assert url.scheme == 'postgresql', "only the postgresql scheme is currently supported"
    uta_connection_defaults = {
        'host': url.hostname,
        'port': url.port or 5432,
        'database': url.path[1:],
        'user': url.username,
        'password': url.password,
    }
else:
    uta_connection_defaults = {
        # Invitae-hosted public instance
        'host': 'uta.invitae.com',
        'port': 5432,
        'database': 'uta',
        'user': 'uta_public',
        'password': 'uta_public',
    }



class TranscriptDB(object):
    """
    Returns a connection to the transcript DB.

    :param host: hostname to connect to (None if local socket)
    :type host: str
    :param user: username to connect as
    :type user: str
    :param password: password (None for no password)
    :type password: str
    :param database: which database to connect to
    :type database: str

    # db = TranscriptDB()
    """

    # The UTA database is under development. For now, rely on views from the (outgoing) transcript database
    # create view uta.tx_info as select G.gene,G.chr,G.strand,T.ac,T.cds_start_i,T.cds_end_i,G.descr,G.summary from transcripts.gene G join transcripts1.transcript T on G.gene=T.gene;
    # create view uta.tx_exons as select TE.ac,TE.ord,TE.name,TE.start_i as t_start_i,TE.end_i as t_end_i,'GRCh37.p10'::text as ref,GE.start_i as g_start_i,GE.end_i as g_end_i,GA.cigar as g_cigar,GA.g_seq_a,GA.t_seq_a from transcripts1.gtx_alignment GA join transcripts1.transcript_exon TE on GA.transcript_exon_id=TE.transcript_exon_id join transcripts1.genomic_exon GE on GA.genomic_exon_id=GE.genomic_exon_id;
    # grant usage on schema uta to PUBLIC; grant select on uta.tx_info to PUBLIC; grant select on uta.tx_exons to PUBLIC;
    tx_seq_sql = 'select gene,ac,seq from uta0.transcript where ac=%(ac)s'
    tx_info_sql = 'select * from uta0.tx_info_v where ac=%(ac)s'
    tx_for_gene_sql = 'select * from uta0.tx_info_v where gene=%(gene)s order by cds_end_i-cds_start_i desc'
    tx_exons_sql = 'select * from uta0.tx_exons_v where ac=%(ac)s and ref=%(ref)s order by g_start_i'

    def __init__(self,
                 host=uta_connection_defaults['host'],
                 port=uta_connection_defaults['port'],
                 database=uta_connection_defaults['database'],
                 user=uta_connection_defaults['user'],
                 password=uta_connection_defaults['password'],
                 ):
        self.logger = logging.getLogger(__name__)
        self.logger.info('connecting to to (host={host}, port={port}, database={database}, user={user}, password={password})...'.format(
            host=host, port=port, database=database, user=user, password=password, ))
        self.conn = psycopg2.connect(host=host, port=port, database=database, user=user, password=password)
        self.cur = self.conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        


    def get_tx_info(self,ac):
        """return transcript info for supplied accession (ac), or None if not found

        :param ac: transcript accession with version (e.g., 'NM_000051.3')
        :type ac: str
        """

        self.cur.execute(self.tx_info_sql,{'ac': ac})
        assert self.cur.rowcount <= 1, 'get_tx_info({ac}) unexpectedly returned {c} rows'.format(
            ac=ac, c=self.cur.rowcount)
        return self.cur.fetchone()        # None if no match

    def get_tx_seq(self,ac):
        """return transcript sequence for supplied accession (ac), or None if not found

        :param ac: transcript accession with version (e.g., 'NM_000051.3')
        :type ac: str
        """

        self.cur.execute(self.tx_seq_sql,{'ac': ac})
        try:
            return self.cur.fetchone()['seq']
        except TypeError:
            # No record for accession
            return None


    def get_tx_exons(self,ac,ref):    
        """
        return transcript info for supplied accession (ac), or None if not found
        
        :param ac: transcript accession with version (e.g., 'NM_000051.3')
        :type ac: str
        :param ref: reference genome ('GRCh37.p10' is the only valid value at this time)
        :type ref: str
        
        # tx_exons = db.get_tx_exons('NM_000051.3','GRCh37.p10')
        # len(tx_exons)
        63
        
        tx_exons have the following attributes::
        
          {'ac': 'NM_000051.3',               # transcript accession
          'ref': 'GRCh37.p10',
          'g_start_i': 108093558,             # genomic start coordinate
          'g_end_i': 108093913,               # genome end coordinate
          'name': '1',
          'ord': 1,
          't_start_i': 0
          't_end_i': 355,
          'g_cigar': '355M',                  # CIGAR string, relative to genome
          'g_seq_a': None,
          't_seq_a': None,
          }
        
        .. note:: chromosome and strand are in the tx_info record
        
        For example:
        
        # tx_exons[0]['ac']
        'NM_000051.3'
        
        """
        self.cur.execute(self.tx_exons_sql,{'ac': ac, 'ref': ref})
        return self.cur.fetchall()        # [] if no match

    def get_tx_for_gene(self,gene):
        """
        return transcript info records for supplied gene, in order of decreasing length

        :param gene: HGNC gene name
        :type gene: str
        """
        self.cur.execute(self.tx_for_gene_sql,{'gene': gene})
        return self.cur.fetchall()


if __name__ == '__main__':
    import logging
    logging.basicConfig(level=logging.DEBUG)
    uta_conn = TranscriptDB()
    tx = uta_conn.get_tx_for_gene('VHL')
    print(tx)

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
