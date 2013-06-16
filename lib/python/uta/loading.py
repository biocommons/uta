from __future__ import absolute_import, division, print_function, unicode_literals

import csv, gzip, itertools, logging
import prettytable

import uta
import uta.sa_models as usam

############################################################################

def create_schema(engine,session,opts,cf):
    """Create and populate initial schema"""
    if opts['--drop-current']:
        session.execute('drop schema if exists '+usam.schema_name+' cascade')
        session.execute('create schema '+usam.schema_name)
        session.execute('alter database uta set search_path = '+usam.schema_name)
        session.commit()

    usam.Base.metadata.create_all(engine)

    session.add(usam.Meta(
            key='schema_version', value=usam.schema_version))


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

def load_gene(engine,session,opts,cf):
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
            origin_id = o.origin_id,
            descr = gi['Full_name_from_nomenclature_authority'],
            maploc = gi['map_location'],
            name = gi['Symbol_from_nomenclature_authority'], 
            )
        session.add(g)
        logging.info('loaded gene {g.name} ({g.descr})'.format(g=g))
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
    import uta.parsers.seqgene

    o_refseq = session.query(usam.Origin).filter(usam.Origin.name == 'RefSeq').one()
    o_seqgene = session.query(usam.Origin).filter(usam.Origin.name == 'seqgene').one()
    

    sg_filter = lambda r: r['transcript'].startswith('NM_') and r['feature_type'] in ['CDS','UTR']
    sgparser = uta.parsers.seqgene.SeqGeneParser(gzip.open(opts['FILE']),
                                                 filter = sg_filter)
    slurp = sorted(list(sgparser), 
                   key = lambda r: (r['transcript'],r['group_label'],r['chr_start'],r['chr_stop']))
    for k,i in itertools.groupby(slurp, key = lambda r: (r['transcript'],r['group_label'])):
        recs = list(i)
        segs = [ (r['feature_type'],int(r['chr_start'])-1,int(r['chr_stop'])) for r in recs ]
        cds_seg_idxs = [ i for i in range(len(segs)) if segs[i][0] == 'CDS' ]
        # merge UTR-CDS and CDS-UTR exons if end of first == start of second
        # prefer this over general adjacent exon merge in case of alignment artifacts
        # last exon
        ei = cds_seg_idxs[-1]
        cds_end_i = segs[ei][2]
        if ei < len(segs)-1:
            if segs[ei][2] == segs[ei+1][1]:
                segs[ei:ei+2] = [('M',segs[ei][1],segs[ei+1][2])]
        # first exon
        ei = cds_seg_idxs[0]
        cds_start_i = segs[ei][1]
        if ei > 0:
            if segs[ei-1][2] == segs[ei][1]:
                segs[ei-1:ei+1] = [('M',segs[ei-1][1],segs[ei][2])]

                
