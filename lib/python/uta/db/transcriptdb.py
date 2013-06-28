import psycopg2, psycopg2.extras, os, urlparse, sys

class TranscriptDB(object):
    # create view uta.tx_info as select G.gene,G.strand,T.ac,T.cds_start_i,T.cds_end_i,G.descr,G.summary from gene G join transcript T on G.gene=T.gene;
    # create view uta.tx_exons as select TE.ac,TE.ord,TE.name,TE.start_i as t_start_i,TE.end_i as t_end_i,'GRCh37.p10'::text as ref,GE.start_i as g_start_i,GE.end_i as g_end_i,GA.cigar as g_cigar,GA.g_seq_a,GA.t_seq_a from gtx_alignment GA join transcript_exon TE on GA.transcript_exon_id=TE.transcript_exon_id join genomic_exon GE on GA.genomic_exon_id=GE.genomic_exon_id;
    tx_info_sql = 'select * from uta.tx_info where ac=%(ac)s'
    tx_for_gene_sql = 'select * from uta.tx_info where gene=%(gene)s order by cds_end_i-cds_start_i desc'
    tx_exons_sql = 'select * from uta.tx_exons where ac=%(ac)s and ref=%(ref)s order by g_start_i'

    def __init__(self, host=None, user=None, password=None, database=None):
        if 'UTA_DB_URL' in os.environ:
            # eg 'psycopg2:///' -- localhost via socket, as user, database=username
            url = urlparse.urlparse(os.environ['UTA_DB_URL'])
            assert url.scheme == 'psycopg2'
            host = url.hostname 
            user = url.username
            password = url.password
            database = url.path[1:]
        elif host is None and user is None and password is None and database is None:
            host = host or 'db.locusdev.net'
            user = user or 'PUBLIC'
            database = database or 'reece'

        self.conn = psycopg2.connect(host = host, user = user, password = password, database = database)
        self.cur = self.conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

    def get_tx_info(self,ac):
        """return transcript info for supplied accession (ac), or None if not found"""
        self.cur.execute(self.tx_info_sql,{'ac': ac})
        assert self.cur.rowcount <= 1, 'get_tx_info({ac}) unexpectedly returned {c} rows'.format(
            ac=ac, c=self.cur.rowcount)
        return self.cur.fetchone()        # None if no match

    def get_tx_exons(self,ac,ref):    
        """return transcript info for supplied accession (ac), or None if not found"""
        self.cur.execute(self.tx_exons_sql,{'ac': ac, 'ref': ref})
        return self.cur.fetchall()        # [] if no match

    def get_tx_for_gene(self,gene):
        """return transcript info records for supplied gene, in order of decreasing length"""
        self.cur.execute(self.tx_for_gene_sql,{'gene': gene})
        return self.cur.fetchall()
