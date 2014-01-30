from __future__ import absolute_import, division, print_function, unicode_literals

import csv
import datetime
import gzip
import hashlib
import itertools
import logging
import os
import time

import eutils.client
    
import uta
import uta.luts
import uta.utils
import uta.formats.geneinfo as ufgi
import uta.formats.exonset as ufes
import uta.formats.txinfo as ufti
usam = uta.models                         # backward compatibility

logger = logging.getLogger(__name__)


############################################################################

def drop_schema(session,opts,cf):
    if session.bind.name == 'postgresql' and usam.use_schema:
        ddl = 'drop schema if exists '+usam.schema_name+' cascade'
        session.execute(ddl)
        session.commit()
        logger.info(ddl)

############################################################################

def create_schema(session,opts,cf):
    """Create and populate initial schema"""

    if session.bind.name == 'postgresql' and usam.use_schema:
        session.execute('create schema '+usam.schema_name)
        session.execute('alter database {db} set search_path = {search_path}'.format(
            db=session.bind.url.database, search_path=usam.schema_name))
        session.execute('set search_path = '+usam.schema_name)
        session.commit()

    usam.Base.metadata.create_all(session.bind)
    session.add(usam.Meta( key='schema_version', value=usam.schema_version ))
    session.add(usam.Meta( key='created', value=datetime.datetime.now().isoformat() ))
    session.commit()
    logger.info('created schema')

############################################################################

def initialize_schema(session,opts,cf):
    """Create and populate initial schema"""

    session.add(
        usam.Origin(
            name='NCBI',
            url = 'http://www.ncbi.nlm.nih.gov/',
            ))
    session.add(
        usam.Origin(
            name='NCBI Gene',
            descr='NCBI gene repository',
            url = 'http://www.ncbi.nlm.nih.gov/gene/',
            url_ac_fmt = 'http://www.ncbi.nlm.nih.gov/gene/{ac}'
            ))
    session.add(
        usam.Origin(
            name='NCBI RefSeq',
            descr='NCBI RefSeq (nuccore) repository',
            url = 'http://www.ncbi.nlm.nih.gov/refseq/',
            url_ac_fmt = 'http://www.ncbi.nlm.nih.gov/nuccore/{ac}'
            ))
    session.add(
        usam.Origin(
            name='NCBI seq_gene',
            descr='NCBI "seq_gene" files from FTP site',
            url = 'ftp://ftp.ncbi.nih.gov/genomes/MapView/Homo_sapiens/sequence/current/initial_release/',
            ))
    
    session.commit()
    logger.info('initialized schema')


############################################################################

def load_seqinfo(session,opts,cf):
    """load Seq entries with accessions from fasta file
    see uta/sbin/fasta-seq-info
    """

    raise RuntimeError("Needs rework for newer seqinfo format (uta.formats.seqinfo)")

    ori = session.query(usam.Origin).filter(usam.Origin.name == opts['--origin']).one()

    fh = gzip.open(opts['FILE'],'r') if opts['FILE'].endswith('.gz') else open(opts['FILE'])
    seqinfo = csv.DictReader(fh, delimiter=b'\t')

    if opts['--fast']:
        logger.info('using fast(er) seq_anno loader')
        data = list(seqinfo)
        unique_md5_lens = set([ (d['md5'],int(d['len'])) for d in data ])
        session.execute(
            usam.Seq.__table__.insert(),
            [ {'seq_id':md5, 'len':len}
              for md5,len in unique_md5_lens ]
            )
        session.execute(
            usam.SeqAnno.__table__.insert(),
            [ {'origin_id': ori.origin_id,'seq_id':d['md5'],'ac':a}
              for d in data for a in d['aliases'].split(',') ]
            )
        session.commit()
        return

    raise RuntimeError("code below probably needs updating")
    for i_row,row in enumerate(seqinfo):
        seq = session.query(usam.Seq).filter(usam.Seq.seq_id == row['md5']).first()
        if seq is None:
            seq = usam.Seq(seq_id=row['md5'],len=row['len'])
            session.add(seq)

        for alias in row['aliases'].split(','):
            soa = session.query(usam.SeqAnno).filter(
                usam.SeqAnno.origin_id == ori.origin_id,
                usam.SeqAnno.ac == alias,
                ).first()
            if soa is None:
                soa = usam.SeqAnno(
                    seq = seq,
                    origin = ori,
                    alias = alias
                    )
                session.add(soa)
        if i_row % 250 == 0:
            session.commit()
            logger.info('commited @ row '+str(i_row))
    session.commit()

############################################################################

def load_exonsets(session,opts,cf):
    seen = set()
    for es in ufes.ExonSetReader(gzip.open(opts['FILE'])):
        seen_key = (es.tx_ac,es.alt_ac,es.method)
        if seen_key in seen:
            logger.warn("multiple occurrences of {seen_key} in {file}; using only first".format(
                seen_key=seen_key, file=opts['FILE']))
            continue
        seen.add(seen_key)
        
        u_es = usam.ExonSet(
            tx_ac=es.tx_ac,
            alt_ac=es.alt_ac,
            alt_aln_method=es.method,
            alt_strand=es.strand
            )
        session.add(u_es)

        exons = [ map(int,ex.split(',')) for ex in es.exons_se_i.split(';') ]
        exons.sort(reverse=es.strand==-1)
        for i_ex,ex in enumerate(exons):
            s,e = ex
            u_ex = usam.Exon(
                exon_set=u_es,
                start_i=s,
                end_i=e,
                ord=i_ex,
                )
            session.add(u_ex)

        session.commit()


############################################################################

def load_geneinfo(session,opts,cf):
    for gi in ufgi.GeneInfoReader(gzip.open(opts['FILE'])):
        session.add(
            usam.Gene(
                hgnc=gi.hgnc,
                maploc=gi.maploc,
                descr=gi.descr,
                summary=gi.summary,
                aliases=gi.aliases,
                ))
    session.commit()

############################################################################

def load_txinfo(session,opts,cf):
    self_aln_method = 'transcript'

    for ti in ufti.TxInfoReader(gzip.open(opts['FILE'])):
        if ti.exons_se_i == '':
            logger.warning(ti.ac + ': no exons?!; skipping.')
            continue

        ori = session.query(usam.Origin).filter(usam.Origin.name == ti.origin).one()
        cds_start_i,cds_end_i = map(int,ti.cds_se_i.split(','))

        u_tx = usam.Transcript(
            ac=ti.ac,
            origin=ori,
            hgnc=ti.hgnc,
            cds_start_i=cds_start_i,
            cds_end_i=cds_end_i,
            )
        session.add(u_tx)

        u_es = usam.ExonSet(
            tx_ac=ti.ac,
            alt_ac=ti.ac,
            alt_strand=1,
            alt_aln_method=self_aln_method,
            )
        session.add(u_es)

        exons = [ map(int,ex.split(',')) for ex in ti.exons_se_i.split(';') ]
        for i_ex,ex in enumerate(exons):
            s,e = ex
            u_ex = usam.Exon(
                exon_set=u_es,
                start_i=s,
                end_i=e,
                ord=i_ex,
                )
            session.add(u_ex)

        session.commit()



############################################################################

aln_sel_sql = """
SELECT * FROM _tx_alt_exon_pairs_v TAEP
WHERE NOT EXISTS (
    SELECT tx_exon_id,alt_exon_id
    FROM exon_aln EA
    WHERE EA.tx_exon_id=TAEP.tx_exon_id AND EA.alt_exon_id=TAEP.alt_exon_id
    )
AND alt_ac in (
'NC_000001.10', 'NC_000002.11', 'NC_000003.11',
'NC_000004.11', 'NC_000005.9', 'NC_000006.11',
'NC_000007.13', 'NC_000008.10', 'NC_000009.11',
'NC_000010.10', 'NC_000011.9', 'NC_000012.11',
'NC_000013.10', 'NC_000014.8', 'NC_000015.9',
'NC_000016.9', 'NC_000017.10', 'NC_000018.9',
'NC_000019.9', 'NC_000020.10', 'NC_000021.8',
'NC_000022.10', 'NC_000023.10', 'NC_000024.9'
)
"""

aln_ins_sql = """
INSERT INTO exon_aln (tx_exon_id,alt_exon_id,cigar,added,tx_aseq,alt_aseq) VALUES (%s,%s,%s,%s,%s,%s)
"""


def fetch_align_tasks(session, opts, cf):
    import psycopg2.extras

    con = session.bind.pool.connect()

    cur = con.cursor(cursor_factory=psycopg2.extras.NamedTupleCursor)
    cur.execute(aln_sel_sql)
    for r in cur.fetchall():
        print("\t".join([ '%s:%d:%d' % (r.tx_ac, r.tx_start_i, r.tx_end_i),
                          '%s:%d:%d' % (r.alt_ac, r.alt_start_i, r.alt_end_i) ]))



def align_exons(session, opts, cf):
    # N.B. setup.py declares dependencies for using uta as a client.  The
    # imports below are loading depenencies only and are not in setup.py.
    import psycopg2.extras
    from eutils.sqlitecache import SQLiteCache
    from bdi.multifastadb import MultiFastaDB
    import uta.utils.genomeutils as uug
    import uta.utils.alignment as uua
    import locus_lib_bio.align.algorithms as llbaa

    aligner = 'llbaa'

    cache = SQLiteCache(os.path.expanduser('~/tmp/align-exons.db'))
    def _align(tx_seq,alt_seq):
        key = aligner + hashlib.md5(tx_seq+';'+alt_seq).hexdigest()
        try:
            a = cache[key]
            logger.debug('cache hit for ({}~{}); key={}'.format(len(tx_seq),len(alt_seq),key))
            return a
        except KeyError:
            logger.debug('cache miss for ({}~{}); key={}'.format(len(tx_seq),len(alt_seq),key))
            pass
        if aligner == '':
            cache[key] = uua.align2(tx_seq,alt_seq)
        elif aligner == 'llbaa':
            score,cigar = llbaa.needleman_wunsch_gotoh_align(tx_seq,alt_seq)
            tx_aseq,alt_aseq = llbaa.cigar_alignment(tx_seq,alt_seq,cigar,hide_match=False)
            cache[key] = tx_aseq,alt_aseq
        else:
            raise RuntimeError("WTF? I ain't ne'er heard of no {} aligner".format(aligner))
        return cache[key]


    mfdb = MultiFastaDB([opts[u'FASTA_DIR']], use_meta_index=True)
    con = session.bind.pool.connect()

    cur = con.cursor(cursor_factory=psycopg2.extras.NamedTupleCursor)
    cur.execute(aln_sel_sql)
    rows = cur.fetchall()
    n_rows = len(rows)
    ac_warning = set()
    t0 = time.time()
    tx_acs = set()
    for i_r,r in enumerate(rows):
        if r.tx_ac in ac_warning or r.alt_ac in ac_warning:
            continue
        try:
            tx_seq = mfdb.fetch(r.tx_ac, r.tx_start_i, r.tx_end_i)
        except KeyError:
            logging.warning("{r.tx_ac}: Not in sequence sources; can't align".format(r=r))
            ac_warning.add(r.tx_ac)
            continue
        try:
            alt_seq = mfdb.fetch(r.alt_ac, r.alt_start_i, r.alt_end_i)
        except KeyError:
            logging.warning("{r.alt_ac}: Not in sequence sources; can't align".format(r=r))
            ac_warning.add(r.alt_ac)
            continue

        if r.alt_strand == -1:
            alt_seq = uug.reverse_complement(alt_seq)

        tx_aseq,alt_aseq = _align(tx_seq,alt_seq)

        cigar = uua.alignment_cigar_string(tx_aseq,alt_aseq)
        added = datetime.datetime.now()
        cur.execute(aln_ins_sql, [r.tx_exon_id,r.alt_exon_id,cigar,added,tx_aseq,alt_aseq])
        tx_acs.add(r.tx_ac)
        if i_r == n_rows-1 or i_r % 50 == 0:
            con.commit()
            speed = (i_r+1) / (time.time() - t0);      # aln/sec
            etr = (n_rows-i_r-1) / speed               # etr in secs
            etr_s = str(datetime.timedelta(seconds=int(etr)))  # etr as H:M:S
            logger.info('{i_r}/{n_rows} {p_r:.1f}%; committed; speed={speed:.1f} aln/sec; etr={etr:.0f}s ({etr_s}); {n_tx} tx ({tx_acs})'.format(
                i_r=i_r,n_rows=n_rows,p_r=i_r/n_rows*100,speed=speed,etr=etr,etr_s=etr_s,n_tx=len(tx_acs),tx_acs=','.join(sorted(tx_acs)) ))
            tx_acs = set()

    cur.close()
    con.close()



def load_ncbi_geneinfo(session, opts, cf):
    """
    import data as downloaded (by you) from 
    ftp://ftp.ncbi.nlm.nih.gov/gene/DATA/gene_info.gz
    """
    import uta.parsers.geneinfo
    
    o = session.query(usam.Origin).filter(usam.Origin.name == 'NCBI Gene').one()
    gip = uta.parsers.geneinfo.GeneInfoParser(gzip.open(opts['FILE']))
    for gi in gip:
        if gi['tax_id'] != '9606' or gi['Symbol_from_nomenclature_authority'] == '-':
            continue
        g = usam.Gene(
            gene_id = gi['GeneID'],
            hgnc = gi['Symbol_from_nomenclature_authority'],
            maploc = gi['map_location'],
            descr = gi['Full_name_from_nomenclature_authority'],
            aliases = gi['Synonyms'],
            strand = gi[''],
            )
        session.add(g)
        logger.info('loaded gene {g.hgnc} ({g.descr})'.format(g=g))
    session.commit()




############################################################################

def load_ncbi_seqgene(session,opts,cf):
    """
    import data as downloaded (by you) as from
    ftp.ncbi.nih.gov/genomes/MapView/Homo_sapiens/sequence/current/initial_release/seq_gene.md.gz
    """
    def _strand_pm_to_int(s):
        return None if s is None else 1 if s is '+' else -1 if s is '-' else None
    
    def _seqgene_recs_to_tx_info(ac,assy,recs):
        ti = {
            'ac': ac,
            'assy': assy,
            'strand': _strand_pm_to_int(recs[0]['chr_orient']),
            'gene_id': int(recs[0]['feature_id'].replace('GeneID:','')) if 'GeneID' in recs[0]['feature_id'] else None,
            }
        segs = [ (r['feature_type'],int(r['chr_start'])-1,int(r['chr_stop'])) for r in recs ]
        cds_seg_idxs = [ i for i in range(len(segs)) if segs[i][0] == 'CDS' ]
        # merge UTR-CDS and CDS-UTR exons if end of first == start of second
        # prefer this over general adjacent exon merge in case of alignment artifacts
        # last exon
        ei = cds_seg_idxs[-1]
        ti['cds_end_i'] = segs[ei][2]
        if ei < len(segs)-1:
            if segs[ei][2] == segs[ei+1][1]:
                segs[ei:ei+2] = [('M',segs[ei][1],segs[ei+1][2])]
        # first exon
        ei = cds_seg_idxs[0]
        ti['cds_start_i'] = segs[ei][1]
        if ei > 0:
            if segs[ei-1][2] == segs[ei][1]:
                segs[ei-1:ei+1] = [('M',segs[ei-1][1],segs[ei][2])]
        ti['exon_se_i'] = [ s[1:3] for s in segs ]
        return ti


    import uta.parsers.seqgene

    o_refseq = session.query(usam.Origin).filter(usam.Origin.name == 'NCBI RefSeq').one()
    o_seqgene = session.query(usam.Origin).filter(usam.Origin.name == 'NCBI seq_gene').one()

    sg_filter = lambda r: (r['transcript'].startswith('NM_')
                           and r['group_label'] == 'GRCh37.p10-Primary Assembly'
                           and r['feature_type'] in ['CDS','UTR'])
    sgparser = uta.parsers.seqgene.SeqGeneParser(gzip.open(opts['FILE']),
                                                 filter = sg_filter)
    slurp = sorted(list(sgparser), 
                   key = lambda r: (r['transcript'],r['group_label'],r['chr_start'],r['chr_stop']))
    for k,i in itertools.groupby(slurp, key = lambda r: (r['transcript'],r['group_label'])):
        ac,assy = k
        ti = _seqgene_recs_to_tx_info(ac,assy,list(i))

        resp = session.query(usam.Transcript).filter(usam.Transcript.ac == ac)
        if resp.count() == 0:
            t = usam.Transcript(ac = ac, origin = o_refseq, gene_id = ti['gene_id'])
            session.add(t)
        else:
            t = resp.one()

        chr_ac = uta.lut.chr_to_NC()
        es = usam.ExonSet(
            transcript_id = t.transcript_id,
            ref_nseq_id = 99,
            strand = ti['strand'],
            cds_start_i = ti['cds_start_i'],
            cds_end_i = ti['cds_end_i'],
            )

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
