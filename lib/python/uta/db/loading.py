from __future__ import absolute_import, division, print_function, unicode_literals

import csv
import datetime
import gzip
import hashlib
import itertools
import logging

import uta
import uta.db.sa_models as usam
import uta.luts

############################################################################

def drop_schema(engine,session,opts,cf):
    if engine.url.drivername == 'postgresql' and usam.use_schema:
        session.execute('drop schema if exists '+usam.schema_name+' cascade')

############################################################################

def create_schema(engine,session,opts,cf):
    """Create and populate initial schema"""

    if engine.url.drivername == 'postgresql' and usam.use_schema:
        if opts['--drop-current']:
            session.execute('drop schema if exists '+usam.schema_name+' cascade')
        session.execute('create schema '+usam.schema_name)
        session.execute('alter database {db} set search_path = {search_path}'.format(
            db=engine.url.database, search_path=usam.schema_name))
        session.execute('set search_path = '+usam.schema_name)
        session.commit()


    usam.Base.metadata.create_all(engine)

    session.add(usam.Meta( key='schema_version', value=usam.schema_version ))
    session.add(usam.Meta( key='created', value=datetime.datetime.now().isoformat() ))

############################################################################

def initialize_schema(engine,session,opts,cf):
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


############################################################################

def load_seq_aliases(engine,session,opts,cf):
    """load Seq entries with accessions from fasta file"""

    logger = logging.getLogger(__package__)

    ori = session.query(usam.Origin).filter(usam.Origin.name == opts['--origin']).one()

    fh = gzip.open(opts['FILE'],'r') if opts['FILE'].endswith('.gz') else open(opts['FILE'])
    seqinfo = csv.DictReader(fh, delimiter=b'\t')
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

def load_eutils_genes(engine,session,opts,cf):
    """
    load genes via eutils

    This is preferred over data in ftp://ftp.ncbi.nlm.nih.gov/gene/DATA/GENE_INFO/ because
    we get summaries with eutils.
    """
    import eutils.client
    
    logger = logging.getLogger(__package__)

    ec = eutils.client.Client()
    u_ori_gene = session.query(usam.Origin).filter(usam.Origin.name == 'NCBI Gene').one()

    for hgnc in opts['GENES']:
        try:
            e_gene = ec.fetch_gene_by_hgnc(hgnc)
        except eutils.exceptions.EutilsError as e:
            logger.exception(e)
            continue

        u_gene = session.query(usam.Gene).filter(usam.Gene.hgnc == hgnc).first()
        if u_gene is None:
            u_gene = usam.Gene(
                gene_id = e_gene.gene_id,
                hgnc = e_gene.hgnc,
                maploc = e_gene.maploc,
                descr = e_gene.description,
                summary = e_gene.summary,
                aliases = ','.join(e_gene.synonyms),
                )
            session.merge(u_gene)
            u_ori_gene.tickle_update()
            session.commit()
            logger.info("Gene: added {u_gene.gene_id} ({u_gene.hgnc}; {u_gene.descr})".format(u_gene=u_gene))

    session.commit()



def load_eutils_transcripts(engine,session,opts,cf):
    pass


def load_eutils_by_gene(engine,session,opts,cf):
    """
    load eutils, starting with a list of genes
    """
    import eutils.client
    
    logger = logging.getLogger(__package__)

    ec = eutils.client.Client()
    u_ori_gene = session.query(usam.Origin).filter(usam.Origin.name == 'NCBI Gene').one()
    u_ori_nt = session.query(usam.Origin).filter(usam.Origin.name == 'NCBI RefSeq').one()

    for hgnc in opts['GENES']:
        e_gene = ec.fetch_gene_by_hgnc(hgnc)

        u_gene = session.query(usam.Gene).filter(usam.Gene.hgnc == hgnc).first()
        if u_gene is None:
            u_gene = usam.Gene(
                gene_id = e_gene.gene_id,
                hgnc = e_gene.hgnc,
                maploc = e_gene.maploc,
                descr = e_gene.description,
                summary = e_gene.summary,
                aliases = ','.join(e_gene.synonyms),
                )
            session.add(u_gene)
            session.commit()
            logger.info("Gene: added {u_gene.gene_id} ({u_gene.hgnc}; {u_gene.descr})".format(u_gene=u_gene))

        for e_ref in e_gene.references:
            # Reference sequence (e.g., NC, NG, NT)

            u_ref_seq = session.query(usam.Seq).join(usam.SeqOriginAlias).filter(
                usam.SeqOriginAlias.alias == e_ref.acv).first()

            if u_ref_seq is None:
                logging.warning("reference sequence {e_ref.acv} ({e_ref.heading}) is not loaded; skipping".format(
                    e_ref=e_ref))
                continue
            
            # loop over transcripts ("products")
            for e_prd in e_ref.products:

                raise RuntimeError('BROKEN HERE')
                # Check ExonSet, not Transcript
                q = session.query(usam.Transcript).filter(usam.Transcript.ac == e_prd.acv)
                if session.query(q.exists()):
                    logger.info("Transcript {e_prd.acv} already exists; skipping".format(e_prd=e_prd))
                    continue

                # fetch RefSeq corresponding to this transcript, or create
                # *based on transcript sequence  md5, not accession*
                e_gbseq = ec.fetch_gbseq_by_ac(e_prd.acv)
                seq_md5 = hashlib.md5(e_gbseq.seq.upper()).hexdigest()
                u_tx_seq = session.query(usam.Seq).filter(usam.Seq.seq_id == seq_md5).first()
                if u_tx_seq is None:
                    u_tx_seq = usam.Seq(
                        seq = e_gbseq.seq.upper()
                        )
                    assert u_tx_seq.seq_id == seq_md5
                    session.add(u_tx_seq)
                    logger.info("Seq: added seq_id {u_tx_seq.seq_id} for alias {e_gbseq.acv} ({e_gbseq.summary})".format(
                        u_ref_seq=u_ref_seq, u_refalias=u_refalias, e_gbseq=e_gbseq))

                # fetch seq_origin_alias record, or create it
                u_tx_seq_alias = session.query(usam.SeqOriginAlias).filter(
                    usam.Seq.seq_id == seq_md5,
                    usam.SeqOriginAlias.alias == e_gbseq.acv).first()
                if u_tx_seq_alias is None:
                    u_tx_seq_alias = usam.SeqOriginAlias(
                        origin=u_ori_nt,
                        seq_id=seq_md5,
                        alias=e_prd.acv,
                        descr=e_gbseq.definition,)
                    session.add(u_tx_seq_alias)
                    session.commit()
                    logger.info("SeqOriginAlias: added alias {u_tx_seq_alias.alias} ({u_tx_seq_alias.descr}) for seq_id {u_tx_seq_alias.seq_id}".format(
                        u_tx_seq_alias=u_tx_seq_alias))

                # we already know that the Transcript doesn't exist 
                u_tx = usam.Transcript(
                    origin=u_ori_nt,
                    gene_id=e_gene.gene_id,
                    seq=u_tx_seq,
                    ac=e_prd.acv,
                    cds_start_i=e_gbseq.cds.start_i,
                    cds_end_id=e_gbseq.cds.end_i,
                    )
                session.add(u_tx)
                logger.info("Transcript: added {u_tx.ac} for gene {u_tx.gene} w/ Seq {u_tx.seq_id}".format(
                        u_tx=u_tx))

                # Add transcript exon set
                u_tx_es = usam.ExonSet(
                    transcript = u_tx,
                    ref_seq = u_tx_seq,
                    origin = u_ori_nt,
                    method = None,
                    strand = 1)           # by definition
                session.add(u_tx_es)
                logger.info("ExonSet: added {ues.ac} for <{u_tx.ac}~{utxex.ref_seq.aliases}, {u_tx_es.origin.name}, {u_tx_es.method}>".format(
                    ues=ues, u_tx=u_tx, e_ref=e_ref))

                import IPython; IPython.embed()

                for exon in gbseq.intervals:
                    ue = usam.Exon(
                        exonset = u_tx_es,
                        start_i = exon.start_i,
                        end_i = exon.end_i)
                    session.add(ue)

                #gc = e_prd.genomic_coords

                session.commit()
                logger.info("** Transcript: added {e_ref.acv}~{e_prd.acv}; {n_exons} exons".format(
                    e_ref=e_ref,e_prd=e_prd,n_exons=len(gc.intervals)))

    session.commit()
############################################################################

def load_gene_info(engine,session,opts,cf):
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

def load_transcripts_gbff(engine,session,opts,cf):
    """
    import data as downloaded (by you) from 
    ftp://ftp.ncbi.nlm.nih.gov/refseq/H_sapiens/mRNA_Prot/human.rna.gbff.gz
    """
    for rec in SeqIO.parse(gzip.open(opts['FILE']),'genbank'):
        if not rec.id.startswith('NM_'):
                continue
        #nseq_id = 
        #t = usam.Transcript(
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
        import IPython; IPython.embed()

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
