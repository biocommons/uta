import uta
import uta.models

############################################################################

def create_schema(engine,session,opts,cf):
    if opts['--drop-current']:
        session.execute('drop schema if exists '+uta.models.schema_name+' cascade')
        session.execute('create schema '+uta.models.schema_name)
        session.execute('alter database uta set search_path = '+uta.models.schema_name)

    session.commit()
    uta.models.Base.metadata.create_all(engine)
    session.add(uta.models.Meta(
            key='schema_version', value=uta.models.schema_version))
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
        g = uta.models.Gene(gene_id=gi['GeneID'], gene=gi['Symbol_from_nomenclature_authority'], 
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
        #t = uta.models.Transcript(
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
    src = ( rec for rec in uta.parsers.seqgene.SeqGeneParser(gzip.open(opts['FILE']))
            if rec['transcript'].startswith('NM_') )
    for key,reciter in itertools.groupby(src, lambda r: r['transcript']):
        recs = list(reciter)
        import IPython; IPython.embed()
        
