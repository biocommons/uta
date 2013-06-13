from __future__ import absolute_import, division, print_function, unicode_literals

import csv, gzip, itertools, logging
import prettytable

import uta
import uta.sa_models as usam

############################################################################

def create_schema(engine,session,opts,cf):
    if opts['--drop-current']:
        session.execute('drop schema if exists '+usam.schema_name+' cascade')
        session.execute('create schema '+usam.schema_name)
        session.execute('alter database uta set search_path = '+usam.schema_name)

    session.commit()
    usam.Base.metadata.create_all(engine)
    session.add(usam.Meta(
            key='schema_version', value=usam.schema_version))
    session.commit()

############################################################################

def load_gene(engine,session,opts,cf):
    """
    import data as downloaded (by you) from 
    ftp://ftp.ncbi.nlm.nih.gov/gene/DATA/gene_info.gz
    """
    import uta.parsers.geneinfo
    gip = uta.parsers.geneinfo.GeneInfoParser(gzip.open(opts['FILE']))
    for gi in gip:
        if gi['tax_id'] != '9606' or gi['Symbol_from_nomenclature_authority'] == '-':
            continue
        g = usam.Gene(gene_id=gi['GeneID'], gene=gi['Symbol_from_nomenclature_authority'], 
                            name=gi['Full_name_from_nomenclature_authority'], maploc=gi['map_location'],
                            chrom=gi['chromosome'], descr=gi['description'])
        session.add(g)
        logging.info('loaded gene {g.gene} ({g.name})'.format(g=g))
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
    cols = [ 'chr_orient','chr_start','chr_stop','feature_type','group_label','transcript' ]
    sg_filter = lambda r: r['transcript'].startswith('NM_') and r['feature_type'] in ['CDS','UTR']
    sgparser = uta.parsers.seqgene.SeqGeneParser(gzip.open(opts['FILE']),
                                                 filter = sg_filter)
    slurp = sorted(list(sgparser), 
                   key = lambda r: (r['transcript'],r['group_label'],r['chr_start'],r['chr_stop']))
    for k,i in itertools.groupby(slurp, key = lambda r: (r['transcript'],r['group_label'])):
        pt = prettytable.PrettyTable(cols)
        pt.padding_width = 1
        for r in i:
            pt.add_row([ r[c] for c in cols ])
        print(k,':')
        print(pt)
