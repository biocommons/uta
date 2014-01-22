from __future__ import absolute_import, division, print_function, unicode_literals

import csv
import datetime
import gzip
import itertools
import logging

import uta
import uta.db.sa_models as usam
import uta.luts

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

def load_dnaseq(engine,session,opts,cf):
    """load DNASeq entries with accessions from fasta file"""
    raise RuntimeError("THIS ISN'T FINISHED")

    from pysam import Fastafile

    logger = logging.getLogger(__package__)
    ori = session.query(usam.Origin).filter(usam.Origin.name == opts['--origin']).one()

    fa = Fastafile(opts['FASTA_FILE'])
    


############################################################################

def load_eutils_by_gene(engine,session,opts,cf):
    """
    load eutils, starting with a list of genes
    """
    import eutils.client
    
    logger = logging.getLogger(__package__)

    ec = eutils.client.Client()
    uori_gene = session.query(usam.Origin).filter(usam.Origin.name == 'NCBI Gene').one()
    uori_nt = session.query(usam.Origin).filter(usam.Origin.name == 'NCBI RefSeq').one()

    for hgnc in opts['GENES']:
        # Gene
        egene = ec.fetch_gene_by_hgnc(hgnc)
        ugene = usam.Gene(
            gene_id = egene.gene_id,
            hgnc = egene.hgnc,
            maploc = egene.maploc,
            descr = egene.description,
            summary = egene.summary,
            aliases = ','.join(egene.synonyms),
            )
        session.merge(ugene)
        session.commit()
        logger.info("Gene: added {ugene.hgnc} ({ugene.descr})".format(ugene=ugene))

        for eref in egene.references:
            # Reference sequence (NC, NG, NT)
            urefseq = session.query(usam.DNASeq).join(usam.DNASeqOriginAlias).filter(
                usam.DNASeqOriginAlias.alias == eref.acv).first()
            if urefseq is None:
                urefseq = usam.DNASeq()
                session.add(urefseq)
                urefalias = usam.DNASeqOriginAlias(
                    origin=uori_nt,
                    dnaseq=urefseq,
                    alias=eref.acv)
                session.add(urefalias)
                session.commit()
                logger.info("DNASeq: added {urefseq.dnaseq_id} for alias {urefalias.alias} ({eref.label})".format(
                    urefseq=urefseq, urefalias=urefalias, eref=eref))
            
            for eprd in eref.products:
                egbseq = ec.fetch_gbseq_by_ac(eprd.acv)

                # Transcript sequence (NM, XM)
                utxseq = session.query(usam.DNASeq).join(usam.DNASeqOriginAlias).filter(
                    usam.DNASeqOriginAlias.alias == eprd.acv).first()
                if utxseq is None:
                    utxseq = usam.DNASeq()
                    session.add(utxseq)
                    utxseqalias = usam.DNASeqOriginAlias(
                        origin=uori_nt,
                        dnaseq=utxseq,
                        alias=eprd.acv,
                        seq=egbseq.sequence,
                        )
                    session.add(utxseqalias)
                    session.commit()
                    logger.info("DNASeq: added {utxseq.dnaseq_id} for alias {utxseqalias.alias} ({egbseq.summary})".format(
                        urefseq=urefseq, urefalias=urefalias, egbseq=egbseq))

                # Transcript (NM)
                utx = usam.Transcript(
                    origin=ori_nt,
                    ac=eprd.acv,
                    gene_id=egene.gene_id,
                    dnaseq=utxseq,
                    cds_start_i=egbseq.cds_start_i,
                    cds_end_id=egbseq.cds_end_i,
                    )
                session.merge(utx)
                session.commit()
                logger.info("Transcript: added {utx.ac} for gene {utx.gene} w/ DNASeq {utx.dnaseq_id}".format(
                        utx=utx))

                # Self ExonSet
                utxes = usam.ExonSet(
                    transcript = utx,
                    ref_dnaseq = utxseq,
                    origin = uori_nt,
                    method = None,
                    strand = 1)           # by definition
                session.merge(utxes)
                session.commit()
                logger.info("ExonSet: added {ues.ac} for <{utx.ac}~{utxex.ref_dnaseq.aliases}, {utxes.origin.name}, {utxes.method}>".format(
                    ues=ues, utx=utx, eref=eref))

                for exon in gbseq.intervals:
                    ue = usam.Exon(
                        exonset = utxes,
                        start_i = exon.start_i,
                        end_i = exon.end_i)
                    session.merge(ue)
#############                    

                gc = eprd.genomic_coords



                logger.info("** Transcript: added {eref.acv}~{eprd.acv}; {n_exons} exons".format(
                    eref=eref,eprd=eprd,n_exons=len(gc.intervals)))

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
