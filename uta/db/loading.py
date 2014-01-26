from __future__ import absolute_import, division, print_function, unicode_literals

import csv
import datetime
import gzip
import hashlib
import itertools
import logging

import eutils.client
    
import uta
import uta.luts
usam = uta.models                         # backward compatibility

logger = logging.getLogger(__name__)

############################################################################

def drop_schema(session,opts,cf):
    if session.bind.name == 'postgresql' and usam.use_schema:
        ddl = 'drop schema if exists '+usam.schema_name+' cascade'
        session.execute(ddl)
        session.commit()
        logging.info(ddl)

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
    logging.info('created schema')

############################################################################

def initialize_schema(session,opts,cf):
    """Create and populate initial schema"""

    session.add(
        usam.Origin(name='NCBI',
                    url = 'http://www.ncbi.nlm.nih.gov/',
                    ))
    session.add(
        usam.Origin(name='NCBI Gene',
                    url = 'http://www.ncbi.nlm.nih.gov/gene/',
                    url_ac_fmt = 'http://www.ncbi.nlm.nih.gov/gene/{ac}'
                    ))
    session.add(
        usam.Origin(name='NCBI RefSeq',
                    url = 'http://www.ncbi.nlm.nih.gov/refseq/',
                    url_ac_fmt = 'http://www.ncbi.nlm.nih.gov/nuccore/{ac}'
                    ))
    session.add(
        usam.Origin(name='NCBI seq_gene',
                    url = 'ftp://ftp.ncbi.nih.gov/genomes/MapView/Homo_sapiens/sequence/current/initial_release/',
                    ))
    
    session.commit()
    logging.info('initialized schema')


############################################################################

def load_seq_info(session,opts,cf):
    """load Seq entries with accessions from fasta file
    see uta/sbin/fasta-seq-info
    """

    ori = session.query(usam.Origin).filter(usam.Origin.name == opts['--origin']).one()

    fh = gzip.open(opts['FILE'],'r') if opts['FILE'].endswith('.gz') else open(opts['FILE'])
    seqinfo = csv.DictReader(fh, delimiter=b'\t')

    if opts['--fast']:
        logger.info('using fast(er) seq_origin_alias loader')
        data = list(seqinfo)
        unique_md5_lens = set([ (d['md5'],int(d['len'])) for d in data ])
        session.execute(
            usam.Seq.__table__.insert(),
            [ {'seq_id':md5, 'len':len} for md5,len in unique_md5_lens ]
            )
        session.execute(
            usam.SeqOriginAlias.__table__.insert(),
            [ {'origin_id': ori.origin_id,'seq_id':d['md5'],'alias':a} for d in data for a in d['aliases'].split(',') ]
            )
        return


    for i_row,row in enumerate(seqinfo):
        seq = session.query(usam.Seq).filter(usam.Seq.seq_id == row['md5']).first()
        if seq is None:
            seq = usam.Seq(seq_id=row['md5'],len=row['len'])
            session.add(seq)

        for alias in row['aliases'].split(','):
            soa = session.query(usam.SeqOriginAlias).filter(
                usam.SeqOriginAlias.origin_id == ori.origin_id,
                usam.SeqOriginAlias.alias == alias,
                ).first()
            if soa is None:
                soa = usam.SeqOriginAlias(
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

def load_eutils_genes(session,opts,cf):
    """
    load genes via eutils

    This is preferred over data in ftp://ftp.ncbi.nlm.nih.gov/gene/DATA/GENE_INFO/ because
    we get summaries with eutils.
    """
    align_method = 'splign'
    self_align_method = 'identity'

    ec = eutils.client.Client()
    u_ori_gene = session.query(usam.Origin).filter(usam.Origin.name == 'NCBI Gene').one()
    u_ori_nt = session.query(usam.Origin).filter(usam.Origin.name == 'NCBI RefSeq').one()

    def _get_or_create_seq(seq):
        logger.debug('***** _get_or_create_seq('+seq[0:10]+'...)')
        seq_md5 = hashlib.md5(seq.upper()).hexdigest()
        u_seq = session.query(usam.Seq).filter(usam.Seq.seq_id == seq_md5).first()
        if u_seq is not None:
            return u_seq,False
        u_seq = usam.Seq(
            seq = seq.upper()
            )
        session.add(u_seq)
        logger.info("Seq: added seq_id {u_seq.seq_id}".format(u_seq=u_seq))
        return u_seq,True
        
    def _get_or_create_gene(hgnc,e_gene=None):
        logger.debug("***** _get_or_create_gene({hgnc},{e_gene})".format(hgnc=hgnc,e_gene=e_gene))
        u_gene = session.query(usam.Gene).filter(usam.Gene.hgnc == hgnc).first()
        if u_gene is not None:
            return u_gene,False
        if e_gene is None:
            e_gene = ec.fetch_gene_by_hgnc(hgnc)
        u_gene = usam.Gene(
            gene_id = e_gene.gene_id,
            hgnc = e_gene.hgnc,
            maploc = e_gene.maploc,
            descr = e_gene.description,
            summary = e_gene.summary,
            aliases = ','.join(e_gene.synonyms),
            )
        session.add(u_gene)
        logger.info("Gene: added {u_gene.gene_id} ({u_gene.hgnc}; {u_gene.descr})".format(u_gene=u_gene))
        return u_gene,True

    def _get_or_create_tx(ac,u_gene=None,e_tx=None):
        logger.debug("***** _get_or_create_tx({ac},{u_gene},{e_tx})".format(
            ac=ac,u_gene=u_gene,e_tx=e_tx))
        u_tx = session.query(usam.Transcript).filter(usam.Transcript.ac == ac).first()
        if u_tx is not None:
            return u_tx,False
        if u_gene is None:
            u_gene,_ = _get_or_create_gene(e_tx.gene)
        if e_tx is None:
            e_tx = ec.fetch_nuccore_by_ac(ac)
        u_tx_seq,_ = _get_or_create_seq(e_tx.seq)
        u_tx = usam.Transcript(
            origin_id=u_ori_nt.origin_id,
            gene=u_gene,
            seq=u_tx_seq,
            ac=e_tx.acv,
            cds_start_i=e_tx.cds.start_i,
            cds_end_i=e_tx.cds.end_i,
            )
        session.add(u_tx)
        logger.info('created Transcript '+str(u_tx.ac))
        return u_tx,True

    def _get_or_create_tx_exon_set(u_tx,e_tx=None):
        logger.debug("***** _get_or_create_tx_exon_set({u_tx},{e_tx})".format(u_tx=u_tx,e_tx=e_tx))
        u_es = session.query(usam.ExonSet).filter(
            usam.ExonSet.transcript_id == u_tx.transcript_id,
            usam.ExonSet.ref_seq_id == u_tx.seq_id,
            usam.ExonSet.origin_id == u_tx.origin_id,
            usam.ExonSet.method == self_align_method,
            ).first()
        if u_es is not None:
            return u_es,False
        if e_tx is None:
            e_tx = ec.fetch_nuccore_by_ac(u_tx.ac)
        u_es = usam.ExonSet(
            transcript_id = u_tx.transcript_id,
            ref_seq_id = u_tx.seq_id,
            origin_id = u_tx.origin_id,
            method = self_align_method,
            ref_strand = 1,
            )
        session.add(u_es)
        for ex in sorted(e_tx.exons):
            session.add( usam.Exon(exon_set = u_es, start_i = ex.start_i, end_i = ex.end_i) )
        session.commit()
        return u_es,True
    
    def _get_or_create_g_exon_set(u_tx,e_ref,e_prd):
        logger.debug("***** _get_or_create_g_exon_set({u_tx},{e_ref},{e_prd})".format(
            u_tx=u_tx,e_ref=e_ref,e_prd=e_prd))
        u_ref_seq = session.query(usam.Seq).join(usam.SeqOriginAlias).filter(
                        usam.SeqOriginAlias.alias == e_ref.acv).first()
        u_es = session.query(usam.ExonSet).filter(
            usam.ExonSet.transcript == u_tx,
            usam.ExonSet.ref_seq == u_ref_seq,
            usam.ExonSet.origin == u_ori_gene,
            usam.ExonSet.method == align_method,
            ).first()
        if u_es is not None:
            return u_es,False
        u_es = usam.ExonSet(
            transcript = u_tx,
            ref_seq = u_ref_seq,
            origin = u_ori_gene,
            method = align_method,
            ref_strand = e_prd.genomic_coords.strand,
            )
        session.add(u_es)
        for s,e in sorted(e_prd.genomic_coords.intervals):
            session.add( usam.Exon(exon_set = u_es, start_i = s, end_i = e) )
        session.commit()
        return u_es,True

    ############################################################################
    # TODO: switch to esr = ec.esearch(db='gene',term='human[orgn] AND "current only"[Filter]')
    if opts['--all']:
        def e_gene_iterator():
            query = 'human[orgn] AND "current only"[Filter]';
            esr = ec.esearch(db='gene',term=query)
            n = esr.count
            for i,id in enumerate(esr.ids):
                e_gene = ec.efetch(db='gene',id=id)
                logger.info("="*70+"\n{i}/{n} ({p:.1f}%): {e_gene.hgnc}...".format(
                    i=i, n=n, p=(i+1)/n*100, e_gene=e_gene))
                yield e_gene
    else:
        def e_gene_iterator():
            hgncs = opts['GENES']
            for i_hgnc,hgnc in enumerate(hgncs):
                e_gene = ec.fetch_gene_by_hgnc(hgnc)
                logger.info("="*70+"\n{i}/{n} ({p:.1f}%): {hgnc}...".format(
                    i=i, n=n, p=(i+1)/n*100, e_gene=e_gene))
                yield e_gene
    
    for e_gene in e_gene_iterator():
        try:
            if e_gene.type != 'protein-coding':
                logging.warning("Skipping {e_gene.hgnc} (not protein coding)".format(e_gene=e_gene))
                continue

            u_gene,_ = _get_or_create_gene(e_gene.hgnc,e_gene)
            if opts['--with-transcripts']:
                for i_e_ref,e_ref in enumerate(e_gene.references):
                    u_ref_seq = session.query(usam.Seq).join(usam.SeqOriginAlias).filter(
                        usam.SeqOriginAlias.alias == e_ref.acv).first()
                    if u_ref_seq is None:
                        logging.warning("reference sequence {e_ref.acv} ({e_ref.heading}) is not loaded; skipping".format(
                            e_ref=e_ref))
                        continue

                    for e_prd in e_ref.products:
                        if not e_prd.acv.startswith('NM_'):
                            logging.info("Skipping {e_prd.acv} (not an NM)".format(e_prd=e_prd))
                            continue
                        e_tx = ec.fetch_nuccore_by_ac(e_prd.acv)
                        u_tx,_ = _get_or_create_tx(e_prd.acv,u_gene=u_gene,e_tx=e_tx)
                        u_tx_es,_ = _get_or_create_tx_exon_set(u_tx,e_tx=e_tx)
                        u_g_es,_ = _get_or_create_g_exon_set(u_tx,e_ref,e_prd)
            session.commit()

        #except eutils.exceptions.EutilsError as e:
        except Exception as e:
            logger.exception(e)
            continue


############################################################################

def load_gene_info(session,opts,cf):
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
        logging.info('loaded gene {g.hgnc} ({g.descr})'.format(g=g))
    session.commit()

    
############################################################################

def load_transcripts_seqgene(session,opts,cf):
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
            origin_id = o_seqgene,
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
