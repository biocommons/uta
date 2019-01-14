# -*- coding: utf-8 -*-

"""
The previous script used to assemble Ensembl data can be found at
https://github.com/biocommons/uta/blob/master/sbin/ensembl-fetch

This script utilises data files downloaded from the Ensembl ftp site rather than direct use of Ensembl APIs

cat Homo_sapiens.GRCh38.cdna.all.fa Homo_sapiens.GRCh38.ncrna.fa  > Homo_sapiens.GRCh38.rna.all.fa
"""

# import modules
import os
import re
from BCBio import GFF
from Bio import SeqIO
import name_to_accession
import time
import copy

start_time = time.time()
# Set OS paths
ROOT = os.path.dirname(os.path.abspath(__file__))
# ftp://ftp.ensembl.org/pub/release-94/fasta/homo_sapiens/cds/
# ftp://ftp.ensembl.org/pub/release-94/fasta/homo_sapiens/pep/
# ftp://ftp.ensembl.org/pub/release-94/fasta/homo_sapiens/ncrna/
FASTA = os.path.join(ROOT, 'fasta')
# ftp://ftp.ensembl.org/pub/release-94/gff3/homo_sapiens/
# ftp://ftp.ensembl.org/pub/release-94/gtf/homo_sapiens
ALIGNMENTS = os.path.join(ROOT, 'alignments')
"""
Note, the GFF3 files do not contain all the required tags, but the formatting of the GTF file uses too many mixed 
delimiters. To-do. Raise request with Ensemble to ask that tags are in the GFF3

Tags include
- CCDS: Flags this transcript as one linked to a CCDS record
- seleno: Flags this transcript has a Selenocysteine edit. Look for the Selenocysteine
feature for the position of this on the genome
- cds_end_NF: the coding region end could not be confirmed
- cds_start_NF: the coding region start could not be confirmed
- mRNA_end_NF: the mRNA end could not be confirmed
- mRNA_start_NF: the mRNA start could not be confirmed.
- basic: the transcript is part of the gencode basic geneset 
"""

# Set static parameters
method = 'genebuild'
pANDe = ROOT.split('/')[-1]
primary_assembly, ensembl_build = pANDe.split('.')

# Create an accession to name dictionary
ac_to_name_list = []
ac_to_name = {}
name_to_ac = {}
alignment_file = os.path.join(ALIGNMENTS, 'Homo_sapiens.%s.%s.chr_patch_hapl_scaff.gff3') % (
primary_assembly, ensembl_build)
aln_handle = open(alignment_file)
# Limiter which identifies the Ensembl tagged lines only (Note Capital E)
limit_info = dict(gff_source=["Ensembl"])
for rec in GFF.parse(aln_handle, limit_info=limit_info):
    ac_to_name_list.append(rec.features[0].qualifiers.get('Alias'))
for a_n in ac_to_name_list:
    if a_n[0] == 'chrM':
        a_n_o = [a_n[1], a_n[0], a_n[2]]
        a_n = a_n_o
    # Filter out primary chromosomes
    try:
        ac_to_name[a_n[2]] = str(a_n[1]).replace('chr', '')
        name_to_ac[str(a_n[1]).replace('chr', '')] = str(a_n[2])
    except IndexError:
        # Filter out listed super_contigs
        if re.match('chr', a_n[0]):
            ac_to_name[a_n[1]] = str(a_n[0])
            name_to_ac[a_n[0]] = str(a_n[1])
        # Filter out listed Alt chromosomes
        elif re.match('HS', a_n[0]) or re.match('HG', a_n[0]):
            accession = name_to_accession.to_accession(a_n[0], primary_assembly)
            if accession is None:
                print 'accession missing for %s' % a_n[0]
                exit()
            else:
                ac_to_name[accession] = str(a_n[0])
                name_to_ac[a_n[0]] = str(accession)
aln_handle.close()

# Parse transcript fasta files into a dictionary
"""
Create a feature dictionary for the transcript fasta data and split the description into a dictionary allowing rapid 
access to all the features. Format:

for key in tx_dict.keys():
    print key
    print tx_dict[key]

ENST00000225964.9
ID: ENST00000225964.9
Name: ENST00000225964.9
Description: 
    {'gene_symbol': 'COL1A1', 
    'ensembl_gene': 'ENSG00000108821.13', 
    'orientation': '-1', 
    'transcript_biotype': 'protein_coding', 
    'gene_biotype': 'protein_coding', 
    'transcript_type': 'cdna', 
    'hgnc_accession': 'HGNC:2197', 
    'description': 'collagen type I alpha 1 chain'}
Number of features: 0
Seq('AGCAGACGGGAGTTTCTCCTCGGGGTCGGAGCAGGAGGCACGCGGAGTGTGAGG...CTT', SingleLetterAlphabet())

"""

in_tx_file = os.path.join(FASTA, 'Homo_sapiens.%s.rna.all.fa') % primary_assembly
in_tx_handle = open(in_tx_file)
tx_dict = SeqIO.to_dict(SeqIO.parse(in_tx_handle, "fasta"))
in_tx_handle.close()
remove_me = []

for keys in tx_dict.keys():
    tx_description = tx_dict[keys].description
    if re.search("gene_symbol:HGNC:", tx_description):  # Source:UniProtKB/Swiss-Prot;
        remove_me.append(keys)
        continue
    tx_description_list = tx_description.split()
    # reformat the description field into a dictionary
    try:
        tx_description_dict = {
            'transcript_type': tx_description_list[1],
            'orientation': tx_description_list[2].split(':')[-1],
            'ensembl_gene': tx_description_list[3].split(':')[-1],
            'gene_biotype': tx_description_list[4].split(':')[-1],
            'transcript_biotype': tx_description_list[5].split(':')[-1],
            'gene_symbol': tx_description_list[6].split(':')[-1],
            'description': tx_description_list[7].split(':')[-1] + ' ' + ' '.join(tx_description_list[8:-2]),
            'hgnc_accession': 'HGNC:%s' % tx_description_list[-1].split(':')[-1][:-1]
        }
    except IndexError:
        tx_description_dict = {
            'transcript_type': tx_description_list[1],
            'orientation': tx_description_list[2].split(':')[-1],
            'ensembl_gene': tx_description_list[3].split(':')[-1],
            'gene_biotype': tx_description_list[4].split(':')[-1],
            'transcript_biotype': tx_description_list[5].split(':')[-1],
            'gene_symbol': tx_description_list[6].split(':')[-1],
            'description': None,
            'hgnc_accession': None
        }
    tx_dict[keys].description = tx_description_dict

# Parse protein fasta files into a dictionary
"""
Create a feature dictionary for the protein fasta data and split the description into a dictionary allowing rapid 
access to all the features. Format:

for key in pep_dict.keys():
    print key
    print pep_dict[key]

ENSP00000225964.5
ID: ENSP00000225964.5
Name: ENSP00000225964.5
Description: {
    'ensembl_transcript': 'ENST00000225964.9', 
    'description': 'collagen description:collagen type I alpha 1 chain', 
    'gene_symbol': 'COL1A1', 
    'ensembl_gene': 'ENSG00000108821.13', 
    'protein_type': 'cdna', 
    'hgnc_accession': 'HGNC:2197', 
    'orientation': '-1'}
Number of features: 0
Seq('MFSFVDLRLLLLLAATALLTHGQEEGQVEGQDEDIPPITCVQNGLRYHDRDVWK...CFL', SingleLetterAlphabet())
"""

in_pep_file = os.path.join(FASTA, 'Homo_sapiens.%s.pep.all.fa') % primary_assembly
in_pep_handle = open(in_pep_file)
pep_dict = SeqIO.to_dict(SeqIO.parse(in_pep_handle, "fasta"))
in_pep_handle.close()

for keys in pep_dict.keys():
    pep_description = pep_dict[keys].description
    pep_description_list = pep_description.split()
    # reformat the description field into a dictionary
    try:
        pep_description_dict = {
            'protein_type': pep_description_list[1],
            'orientation': pep_description_list[2].split(':')[-1],
            'ensembl_gene': pep_description_list[3].split(':')[-1],
            'ensembl_transcript': pep_description_list[4].split(':')[-1],
            'gene_symbol': pep_description_list[7].split(':')[-1],
            'description': pep_description_list[8].split(':')[-1] + ' ' + ' '.join(pep_description_list[9:-2]),
            'hgnc_accession': 'HGNC:%s' % pep_description_list[-1].split(':')[-1][:-1]
        }
    except IndexError:
        pep_description_dict = {
            'protein_type': pep_description_list[1],
            'orientation': pep_description_list[2].split(':')[-1],
            'ensembl_gene': pep_description_list[3].split(':')[-1],
            'ensembl_transcript': pep_description_list[4].split(':')[-1],
            'gene_symbol': pep_description_list[7].split(':')[-1],
            'description': None,
            'hgnc_accession': None
        }
    pep_dict[keys].description = pep_description_dict

# Create super-dictionary to store data
"""
Merge the transcript and protein data into a super dictionary

Format:
ENST00000225964.9
{
'transcript_data': 
    SeqRecord(seq=Seq('AGCAGACGGGAGTTTCTCCTCGGGGTCGGAGCAGGAGGCACGCGGAGTGTGAGG...CTT', SingleLetterAlphabet()), 
    id='ENST00000225964.9', name='ENST00000225964.9', 
    description={
        'gene_symbol': 'COL1A1', 
        'ensembl_gene': 'ENSG00000108821.13', 
        'orientation': '-1', 
        'transcript_biotype': 'protein_coding', 
        'gene_biotype': 'protein_coding', 
        'transcript_type': 'cdna', 
        'hgnc_accession': 'HGNC:2197', 
        'description': 'collagen type I alpha 1 chain'}, 
    dbxrefs=[]), 
'protein_data': 
    SeqRecord(seq=Seq('MFSFVDLRLLLLLAATALLTHGQEEGQVEGQDEDIPPITCVQNGLRYHDRDVWK...CFL', SingleLetterAlphabet()), 
    id='ENSP00000225964.5', 
    name='ENSP00000225964.5', 
    description={
        'ensembl_transcript': 'ENST00000225964.9',
        'description': 'collagen type I alpha 1 chain',
        'gene_symbol': 'COL1A1', 
        'ensembl_gene': 'ENSG00000108821.13', 
        'protein_type': 'cdna', 
        'hgnc_accession': 'HGNC:2197', 
        'orientation': '-1'}, 
    dbxrefs=[])
}

Note: ncRNAs have 'protein_data' value of None
"""

super_dict = {}
for pep in pep_dict.keys():
    super_dict[pep_dict[pep].description['ensembl_transcript']] = {
        'transcript_data': None,
        'protein_data': pep_dict[pep]
    }

for tx in tx_dict.keys():
    try:
        super_dict[tx]['transcript_data'] = tx_dict[tx]
    except KeyError:
        super_dict[tx] = {
            'transcript_data': tx_dict[tx],
            'protein_data': None}

# Remove the invalid entries that do not have a correctly defined gene symbol - see line 106
for entry_key in remove_me:
    del super_dict[entry_key]

# Add alignment data
"""
Format:


ENST00000225964.9
{'alignment_data': {'utr_cds': [['NC_000017.11', '50183289', '50185501', 'three_prime_UTR'], ['NC_000017.11', '50185502', '50185648', 'CDS'], ['NC_000017.11', '50185778', '50186020', 'CDS'], ['NC_000017.11', '50186317', '50186507', 'CDS'], ['NC_000017.11', '50186640', '50186922', 'CDS'], ['NC_000017.11', '50187015', '50187122', 'CDS'], ['NC_000017.11', '50187484', '50187537', 'CDS'], ['NC_000017.11', '50187876', '50187983', 'CDS'], ['NC_000017.11', '50188096', '50188149', 'CDS'], ['NC_000017.11', '50188530', '50188637', 'CDS'], ['NC_000017.11', '50188742', '50188795', 'CDS'], ['NC_000017.11', '50188903', '50189010', 'CDS'], ['NC_000017.11', '50189168', '50189275', 'CDS'], ['NC_000017.11', '50189377', '50189538', 'CDS'], ['NC_000017.11', '50189679', '50189732', 'CDS'], ['NC_000017.11', '50189859', '50189912', 'CDS'], ['NC_000017.11', '50190001', '50190108', 'CDS'], ['NC_000017.11', '50190327', '50190380', 'CDS'], ['NC_000017.11', '50190543', '50190596', 'CDS'], ['NC_000017.11', '50190817', '50190924', 'CDS'], ['NC_000017.11', '50191383', '50191490', 'CDS'], ['NC_000017.11', '50191788', '50191886', 'CDS'], ['NC_000017.11', '50191980', '50192024', 'CDS'], ['NC_000017.11', '50192475', '50192528', 'CDS'], ['NC_000017.11', '50192640', '50192693', 'CDS'], ['NC_000017.11', '50192797', '50192850', 'CDS'], ['NC_000017.11', '50192994', '50193047', 'CDS'], ['NC_000017.11', '50193943', '50194041', 'CDS'], ['NC_000017.11', '50194130', '50194183', 'CDS'], ['NC_000017.11', '50194349', '50194447', 'CDS'], ['NC_000017.11', '50194573', '50194626', 'CDS'], ['NC_000017.11', '50194721', '50194828', 'CDS'], ['NC_000017.11', '50195047', '50195100', 'CDS'], ['NC_000017.11', '50195232', '50195330', 'CDS'], ['NC_000017.11', '50195434', '50195478', 'CDS'], ['NC_000017.11', '50195567', '50195665', 'CDS'], ['NC_000017.11', '50195923', '50195976', 'CDS'], ['NC_000017.11', '50196155', '50196199', 'CDS'], ['NC_000017.11', '50196314', '50196367', 'CDS'], ['NC_000017.11', '50196484', '50196528', 'CDS'], ['NC_000017.11', '50196617', '50196670', 'CDS'], ['NC_000017.11', '50197010', '50197063', 'CDS'], ['NC_000017.11', '50197180', '50197233', 'CDS'], ['NC_000017.11', '50197732', '50197785', 'CDS'], ['NC_000017.11', '50197949', '50198002', 'CDS'], ['NC_000017.11', '50198161', '50198205', 'CDS'], ['NC_000017.11', '50198433', '50198504', 'CDS'], ['NC_000017.11', '50199226', '50199327', 'CDS'], ['NC_000017.11', '50199418', '50199453', 'CDS'], ['NC_000017.11', '50199556', '50199590', 'CDS'], ['NC_000017.11', '50199753', '50199947', 'CDS'], ['NC_000017.11', '50201411', '50201513', 'CDS'], ['NC_000017.11', '50201514', '50201632', 'five_prime_UTR']], 'exons': [['NC_000017.11', '50183289', '50185648', 'exon'], ['NC_000017.11', '50185778', '50186020', 'exon'], ['NC_000017.11', '50186317', '50186507', 'exon'], ['NC_000017.11', '50186640', '50186922', 'exon'], ['NC_000017.11', '50187015', '50187122', 'exon'], ['NC_000017.11', '50187484', '50187537', 'exon'], ['NC_000017.11', '50187876', '50187983', 'exon'], ['NC_000017.11', '50188096', '50188149', 'exon'], ['NC_000017.11', '50188530', '50188637', 'exon'], ['NC_000017.11', '50188742', '50188795', 'exon'], ['NC_000017.11', '50188903', '50189010', 'exon'], ['NC_000017.11', '50189168', '50189275', 'exon'], ['NC_000017.11', '50189377', '50189538', 'exon'], ['NC_000017.11', '50189679', '50189732', 'exon'], ['NC_000017.11', '50189859', '50189912', 'exon'], ['NC_000017.11', '50190001', '50190108', 'exon'], ['NC_000017.11', '50190327', '50190380', 'exon'], ['NC_000017.11', '50190543', '50190596', 'exon'], ['NC_000017.11', '50190817', '50190924', 'exon'], ['NC_000017.11', '50191383', '50191490', 'exon'], ['NC_000017.11', '50191788', '50191886', 'exon'], ['NC_000017.11', '50191980', '50192024', 'exon'], ['NC_000017.11', '50192475', '50192528', 'exon'], ['NC_000017.11', '50192640', '50192693', 'exon'], ['NC_000017.11', '50192797', '50192850', 'exon'], ['NC_000017.11', '50192994', '50193047', 'exon'], ['NC_000017.11', '50193943', '50194041', 'exon'], ['NC_000017.11', '50194130', '50194183', 'exon'], ['NC_000017.11', '50194349', '50194447', 'exon'], ['NC_000017.11', '50194573', '50194626', 'exon'], ['NC_000017.11', '50194721', '50194828', 'exon'], ['NC_000017.11', '50195047', '50195100', 'exon'], ['NC_000017.11', '50195232', '50195330', 'exon'], ['NC_000017.11', '50195434', '50195478', 'exon'], ['NC_000017.11', '50195567', '50195665', 'exon'], ['NC_000017.11', '50195923', '50195976', 'exon'], ['NC_000017.11', '50196155', '50196199', 'exon'], ['NC_000017.11', '50196314', '50196367', 'exon'], ['NC_000017.11', '50196484', '50196528', 'exon'], ['NC_000017.11', '50196617', '50196670', 'exon'], ['NC_000017.11', '50197010', '50197063', 'exon'], ['NC_000017.11', '50197180', '50197233', 'exon'], ['NC_000017.11', '50197732', '50197785', 'exon'], ['NC_000017.11', '50197949', '50198002', 'exon'], ['NC_000017.11', '50198161', '50198205', 'exon'], ['NC_000017.11', '50198433', '50198504', 'exon'], ['NC_000017.11', '50199226', '50199327', 'exon'], ['NC_000017.11', '50199418', '50199453', 'exon'], ['NC_000017.11', '50199556', '50199590', 'exon'], ['NC_000017.11', '50199753', '50199947', 'exon'], ['NC_000017.11', '50201411', '50201632', 'exon']], 'transcript_info': {'Name': 'COL1A1-201', 'Parent': 'ENSG00000108821', 'tag': 'basic', 'biotype': 'protein_coding', 'version': '9', 'ccdsid': 'CCDS11561.1', 'transcript_id': 'ENST00000225964.9', 'ID': 'ENST00000225964', 'transcript_support_level': '1'}}, 'transcript_data': SeqRecord(seq=Seq('AGCAGACGGGAGTTTCTCCTCGGGGTCGGAGCAGGAGGCACGCGGAGTGTGAGG...CTT', SingleLetterAlphabet()), id='ENST00000225964.9', name='ENST00000225964.9', description={'gene_symbol': 'COL1A1', 'ensembl_gene': 'ENSG00000108821.13', 'orientation': '-1', 'transcript_biotype': 'protein_coding', 'gene_biotype': 'protein_coding', 'transcript_type': 'cdna', 'hgnc_accession': 'HGNC:2197', 'description': 'collagen type I alpha 1 chain'}, dbxrefs=[]), 'protein_data': SeqRecord(seq=Seq('MFSFVDLRLLLLLAATALLTHGQEEGQVEGQDEDIPPITCVQNGLRYHDRDVWK...CFL', SingleLetterAlphabet()), id='ENSP00000225964.5', name='ENSP00000225964.5', description={'ensembl_transcript': 'ENST00000225964.9', 'description': 'collagen type I alpha 1 chain', 'gene_symbol': 'COL1A1', 'ensembl_gene': 'ENSG00000108821.13', 'protein_type': 'pep', 'hgnc_accession': 'HGNC:2197', 'orientation': '-1'}, dbxrefs=[])}
"""

aln_handle = open(alignment_file)
aln_data = aln_handle.read()
aln_data = aln_data.split('\n')
aln_handle.close()

# Progress variables
current_transcript = [None, None]
line_count = 0
omitted_transcripts = {}
for rec in aln_data:
    line_count = line_count + 1
    # Filter out unwanted lines
    if re.match('#', rec):
        continue
    if rec == '':
        continue
    dat = rec.split('\t')
    if dat[2] == 'biological_region':
        continue
    if dat[2] == 'chromosome':
        continue
    if dat[2] == 'supercontig':
        contig_search = dat[8].split(';')
        alias, refseq_id = contig_search[-1].split(',')
        ensembl_alias = dat[0]
        name_to_ac[ensembl_alias] = refseq_id
        continue

    # Remove whitespace from line (SIGH!!!!!)
    dat[8] = dat[8].replace(' ', '_')

    # Format CHR_HG correctly
    if re.match('CHR_HG', dat[0]) or re.match('CHR_HS', dat[0]):
        dat[0] = dat[0].replace('CHR_', '')
    if re.match('MT', dat[0]):
        dat[0] = 'M'

    # Dictionary the data
    dat_dict = {
        'chr': dat[0],
        'designation': dat[2],
        'start': dat[3],
        'end': dat[4],
        'orientation': dat[6],
        'info': dat[8].split(';')
    }
    # Handle line by feature type
    if re.match('ID=gene', dat_dict['info'][0]):
        continue
    elif re.match('ID=transcript', dat_dict['info'][0]):
        # Extract transcript information and add to super_dict
        dat_dict_info = {}
        for info in dat_dict['info']:
            if re.search(':', info):
                assemble, me = info.split('=')
                me = me.split(':')[-1]
                dat_dict_info[assemble] = me
            else:
                assemble, me = info.split('=')
                dat_dict_info[assemble] = me
        try:
            dat_dict_info['tag']
        except KeyError:
            dat_dict_info['tag'] = None
        # Add version to transcript id
        dat_dict_info['transcript_id'] = dat_dict_info['transcript_id'] + '.' + dat_dict_info['version']
        dat_dict['info'] = dat_dict_info
        # Update current_transcript
        current_transcript[0] = dat_dict['info']['transcript_id'].split('.')[0]
        current_transcript[1] = dat_dict['info']['transcript_id']
        # Some transcripts are not contained in the super_dictionary
        try:
            super_dict[dat_dict['info']['transcript_id']]['alignment_data'] = {'transcript_info': dat_dict['info'],
                                                                               'exons': [],
                                                                               'utr_cds': []}
        except KeyError:
            # Store omitted transcript record for further analysis
            omitted_transcripts[dat_dict['info']['transcript_id']] = dat_dict['info']
        continue
    # This section will pick-up exons and UTRs but not CDS
    elif re.match('Parent=transcript', dat_dict['info'][0]):
        # Sanity check
        tx_now = dat_dict['info'][0].replace('Parent=transcript:', '')
        if tx_now != current_transcript[0]:
            print 'Transcript ID %s is not following on ordered flow for the feature on line %s' \
                  % (current_transcript[0], str(line_count))
            exit()
        else:
            tx_v = current_transcript[1]
        # What is the structure type?
        structure_type = dat_dict['designation']
        if structure_type != 'exon' and structure_type != 'five_prime_UTR' and structure_type != 'three_prime_UTR':
            print 'Inappropriate structure identified for Transcript ID %s is on line %s' \
                  % (current_transcript[0], str(line_count))
            exit()
        try:
            if structure_type == 'exon':
                accession = name_to_ac[dat_dict['chr']]
                super_dict[tx_v]['alignment_data']['exons'].append([accession, dat_dict['start'], dat_dict['end'],
                                                                    structure_type])
            else:
                super_dict[tx_v]['alignment_data']['utr_cds'].append([accession, dat_dict['start'], dat_dict['end'],
                                                                      structure_type])
        except KeyError:
            continue
        continue
    elif re.match('ID=CDS', dat_dict['info'][0]):
        # Sanity check
        tx_now = dat_dict['info'][1].replace('Parent=transcript:', '')
        if tx_now != current_transcript[0]:
            print 'Transcript ID %s is not following on ordered flow for the feature on line %s' \
                  % (current_transcript[0], str(line_count))
            exit()
        else:
            tx_v = current_transcript[1]
        # What is the structure type?
        structure_type = dat_dict['designation']
        if structure_type != 'CDS':
            print 'Inappropriate structure identified for Transcript ID %s is on line %s' \
                  % (current_transcript[0], str(line_count))
        accession = name_to_ac[dat_dict['chr']]
        try:
            super_dict[tx_v]['alignment_data']['utr_cds'].append([accession, dat_dict['start'], dat_dict['end'],
                                                                  structure_type])
        except KeyError:
            continue
    # Other line types
    else:
        print 'Unhandled record type identified on line %s' % str(line_count)
        print dat_dict['info']
        exit()
aln_handle.close()

# Sanity check omitted types
om_type = {}
print '\nReference sequences in the following biotype categories have been ommitted'
for om in omitted_transcripts.keys():
    str(omitted_transcripts[om]['biotype'])
    try:
        om_type[omitted_transcripts[om]['biotype']].append(om)
    except KeyError:
        om_type[omitted_transcripts[om]['biotype']] = []
        om_type[omitted_transcripts[om]['biotype']].append(om)
for ty in om_type.keys():
    print ty
print '\n'

# Sanity check omitted types
om_type = {}
print '\nReference sequences in the following biotype categories have been ommitted'
for om in omitted_transcripts.keys():
    str(omitted_transcripts[om]['biotype'])
    try:
        om_type[omitted_transcripts[om]['biotype']].append(om)
    except KeyError:
        om_type[omitted_transcripts[om]['biotype']] = []
        om_type[omitted_transcripts[om]['biotype']].append(om)
for ty in om_type.keys():
    print ty
print '\n'

# Extract the tags from the GTF file
tag_file = os.path.join(ALIGNMENTS, 'Homo_sapiens.%s.%s.chr_patch_hapl_scaff.gtf') % (primary_assembly, ensembl_build)
tag_handle = open(tag_file)
tag_data = tag_handle.read()
tag_data = tag_data.split('\n')
tag_handle.close()
tags_for_tx = {}
for line in tag_data:
    if re.match('#', line):
        continue
    else:
        listed = line.split('\t')
        try:
            listed[2]
        except IndexError:
            if listed == ['']:
                continue
        if listed[2] == 'transcript':

            tag_types = {
                'CCDS': False,
                'seleno': False,
                'cds_end_NF': False,
                'cds_start_NF': False,
                'mRNA_end_NF': False,
                'mRNA_start_NF': False,
                'basic': False
            }

            tx_tag_line = listed[8].replace(' ', '')
            tx_tag_list = tx_tag_line.split(';')
            tx_id = tx_tag_list[2].replace('transcript_id"', '') + tx_tag_list[3].replace('transcript_version"', '.')
            tx_id = tx_id.replace('"', '')
            for a_tag in tag_types.keys():
                if re.search(a_tag, tx_tag_line):
                    tag_types[a_tag] = True
            tags_for_tx[tx_id] = tag_types
        else:
            continue

"""
This loop gathers the data from the dictionary into a single list which will be used to compile the output files
"""


def getKey(item):
    return item[1]


secondary_omission = {}
hgnc_listing = []
title_list = ['tx_ac', 'hgnc', 'hgnc_accession', 'strand', 'tx_description', 'pro_ac', 'gencode_tag', 'tsl', 'alt_ac',
              'exons_se_i', 'tx_se_i', 'cds_s_e', 'sequence', 'origin', 'method']

for tx in super_dict.keys():
    current_tx_list = ([tx, super_dict[tx]['transcript_data'].description['gene_symbol'],
                        super_dict[tx]['transcript_data'].description['hgnc_accession'],
                        super_dict[tx]['transcript_data'].description['orientation'],
                        super_dict[tx]['transcript_data'].description['description']])
    if super_dict[tx]['protein_data'] is None:
        current_tx_list = current_tx_list + [None]
    else:

        # Internal sanity check
        if super_dict[tx]['protein_data'].description['ensembl_transcript'] != tx:
            print 'tx cross ref error %s : %s' % (super_dict[tx]['protein_data'].id, tx)
            continue
        else:
            current_tx_list = current_tx_list + [super_dict[tx]['protein_data'].id]

    # Add transcript support and basic tags as required
    try:
        support_levels = [super_dict[tx]['alignment_data']['transcript_info']['tag'],
                          super_dict[tx]['alignment_data']['transcript_info']['transcript_support_level']]
    except KeyError:
        secondary_omission[tx] = super_dict[tx]
        continue
    current_tx_list = current_tx_list + support_levels

    # Add exonset
    try:
        exonset_list = super_dict[tx]['alignment_data']['exons']
        exonset_int_list = []
        for str_values in exonset_list:
            str_values[1] = int(str_values[1])
            str_values[2] = int(str_values[2])
            exonset_int_list.append(str_values)
        exonset_list = copy.copy(exonset_int_list)

        # reverse the list if transcript is antisense to the chromosome
        if current_tx_list[3] == '-1':
            exonset_list = sorted(exonset_list, key=lambda x: x[1], reverse=True)

        # extract data
        genomic_accession = exonset_list[0][0]
        sets = []
        for exon in exonset_list:
            ex_range = str(int(exon[1]) - 1) + ',' + str(exon[2])
            sets.append(ex_range)
        sets = ';'.join(sets)
        exonset = [genomic_accession, sets]
        current_tx_list = current_tx_list + exonset
    except KeyError:
        secondary_omission[tx] = super_dict[tx]
        continue

    # Add txinfo
    try:
        txinfo_list = super_dict[tx]['alignment_data']['exons']
        int_tx_info_list = []
        for str_values in txinfo_list:
            str_values[1] = int(str_values[1])
            str_values[2] = int(str_values[2])
            int_tx_info_list.append(str_values)
        txinfo_list = copy.copy(int_tx_info_list)

        # reverse the list if transcript is antisense to the chromosome
        if current_tx_list[3] == '-1':
            txinfo_list = sorted(txinfo_list, key=lambda x: x[1], reverse=True)

        # Create the exon boundaries
        absolute_genomic_start = int(txinfo_list[0][1])
        bounds = []
        current_position = 0
        counter = 0
        for tx_ex in txinfo_list:
            counter = counter + 1
            if counter == 1:
                ex_st = int(tx_ex[1]) - absolute_genomic_start
                ex_ed = (int(tx_ex[2]) - absolute_genomic_start) + 1
                current_position = ex_ed
            else:
                ex_st = current_position
                ex_ed = current_position + ((int(tx_ex[2]) - int(tx_ex[1])) + 1)
                current_position = ex_ed
            groups = str(ex_st) + ',' + str(ex_ed)
            bounds.append(groups)
        bounds = ';'.join(bounds)
        current_tx_list = current_tx_list + [bounds]

        # Add cds start and end
        utr_5 = []
        utr_3 = []
        cds_list = super_dict[tx]['alignment_data']['utr_cds']

        for tx_ex in cds_list:
            if tx_ex[-1] == 'five_prime_UTR':
                utr_5.append(tx_ex)
            if tx_ex[-1] == 'three_prime_UTR':
                utr_3.append(tx_ex)
        five_utr_length = 0
        for fives in utr_5:
            five_utr_length = five_utr_length + ((int(fives[2]) - int(fives[1])) + 1)
        three_utr_length = 0
        for threes in utr_3:
            three_utr_length = three_utr_length + ((int(threes[2]) - int(threes[1])) + 1)
        tx_length = 0
        for ex in cds_list:
            tx_length = tx_length + ((int(ex[2]) - int(ex[1])) + 1)
        cds_s_e = ','.join([str(five_utr_length), str((tx_length - three_utr_length) + 0)])
        current_tx_list = current_tx_list + [cds_s_e]
    except KeyError:
        secondary_omission[tx] = super_dict[tx]
        continue
    except IndexError:  # No CDS list i.e. ought to be non-coding
        try:
            txinfo_list = super_dict[tx]['alignment_data']['exons']
            int_tx_info_list = []
            for str_values in txinfo_list:
                str_values[1] = int(str_values[1])
                str_values[2] = int(str_values[2])
                int_tx_info_list.append(str_values)
            txinfo_list = copy.copy(int_tx_info_list)

            # reverse the list if transcript is antisense to the chromosome
            if current_tx_list[3] == '-1':
                txinfo_list = sorted(txinfo_list, key=lambda x: x[1], reverse=True)

            # Create the exon boundaries
            absolute_genomic_start = int(txinfo_list[0][1])
            bounds = []
            current_position = 0
            counter = 0
            for tx_ex in txinfo_list:
                counter = counter + 1
                if counter == 1:
                    ex_st = int(tx_ex[1]) - absolute_genomic_start
                    ex_ed = (int(tx_ex[2]) - absolute_genomic_start) + 1
                    current_position = ex_ed
                else:
                    ex_st = current_position
                    ex_ed = current_position + ((int(tx_ex[2]) - int(tx_ex[1])) + 1)
                    current_position = ex_ed
                groups = str(ex_st) + ',' + str(ex_ed)
                bounds.append(groups)
            bounds = ';'.join(bounds)
            current_tx_list = current_tx_list + [bounds, None]
        except KeyError:
            secondary_omission[tx] = super_dict[tx]
            continue
    # Add sequence
    current_tx_list = current_tx_list + [str(super_dict[tx]['transcript_data'].seq)]

    # Add source information
    current_tx_list = current_tx_list + ['ensembl-' + str(ensembl_build)]

    # Add method
    current_tx_list = current_tx_list + [method]

    # Append to list
    hgnc_listing.append(current_tx_list)

# Open files for writing
OUTPUT = os.path.join(ROOT, 'output')
fasta_handle = os.path.join(OUTPUT, 'fasta')
fasta = open(fasta_handle, 'w')
exonset_handle = os.path.join(OUTPUT, 'exonset')
exonset = open(exonset_handle, 'w')
txinfo_handle = os.path.join(OUTPUT, 'txinfo')
txinfo = open(txinfo_handle, 'w')
assocacs_handle = os.path.join(OUTPUT, 'assocacs')
assocacs = open(assocacs_handle, 'w')

# Weird transcript reporting
three_and_five = os.path.join(ROOT, '3_5_incomplete.txt')
tf_out = open(three_and_five, 'w')
five_ = os.path.join(ROOT, '5_incomplete.txt')
f_out = open(five_, 'w')
three_ = os.path.join(ROOT, '3_incomplete.txt')
t_out = open(three_, 'w')

hgnc_listing = sorted(hgnc_listing, key=getKey)
hgnc_listing = [title_list] + hgnc_listing
out_count = 0

# The following tx biotypes are potentially coding. If False, the CDS for all tx in the category will be removed
coding_tx = {"IG_C_gene": True, #
            "IG_D_gene": True, #
            "IG_J_gene": True, #
            "IG_V_gene": True,#
            "TR_gene": True,
            "nonsense_mediated_decay": True,#
            "polymorphic_pseudogene": True,
            "protein_coding": True,#
            "IG_Z_gene": True,
            "IG_M_gene": True,
            "TR_V_gene": True,#
            "TR_C_gene": True,#
            "TR_J_gene": True,#
            "TR_D_gene": True,#
            "IG_LV_gene": True,
            "non_stop_decay": False,#
            "nontranslating_CDS": False,
            "unknown_likely_coding": True
            }

# These filters are too scrict!
gencode_basic_filter = False
expected_orf_structure = False

# Transcriptstagged as CDS incomplete (5' or 3' = NF)
filter_by_tags = True # If True, filtering by tags occurrs.
kill_by_tags = True # If true, filter_by_tags removes the record from the dataset. If false, the CDS is removed

for tx_information in hgnc_listing:
    out_count = out_count + 1
    # Add header line
    if out_count == 1:
        esl = [tx_information[0], tx_information[8], tx_information[-1], tx_information[3], tx_information[9]]
        eslo = '\t'.join(esl)
        eslo = eslo + '\n'
        exonset.write(eslo)
        # Correct for NC RNA
        til = [tx_information[-2], tx_information[0], tx_information[1], str(tx_information[-4]), tx_information[-5]]
        tilo = '\t'.join(til)
        tilo = tilo + '\n'
        txinfo.write(tilo)
        asl = ['hgnc', tx_information[0], tx_information[5], tx_information[-2]]
        aslo = '\t'.join(asl)
        aslo = aslo + '\n'
        assocacs.write(aslo)
        continue

    # Miss-labelled chr Names so no exonset data???
    if tx_information[8] is None:
        continue

    if gencode_basic_filter is True:
        if tx_information[6] == 'basic':
            continue

    # Filter by biotype
    tx_biotype = super_dict[tx_information[0]]['transcript_data'].description['transcript_biotype']
    if tx_biotype in coding_tx.keys():
        if coding_tx[tx_biotype] is False:
            tx_information[11] = '0,0'

    # Filter by tags
    if filter_by_tags is True:
        tx_id = tx_information[0]
        if tags_for_tx[tx_id]['cds_start_NF'] is True or tags_for_tx[tx_id]['cds_end_NF'] is True:
            if kill_by_tags is False:
                tx_information[11] = '0,0'
            else:
                continue

    # Remove non ATG start and not Ter codon end - i.e. filter out cds incomplete
    if str(tx_information[11]) != 'None' and str(tx_information[11]) != '0,0':
        reference_sequence = tx_information[12]
        cds_start, cds_end = tx_information[11].split(',')
        start_cds = reference_sequence[int(cds_start):int(cds_start) + 3]
        end_cds = reference_sequence[int(cds_end) - 3:int(cds_end)]
        exon_starting_ending = tx_information[11].split(',')
        exon_ending = exon_starting_ending[-1]
        exon_starting = exon_starting_ending[0]
        cds_slice = reference_sequence[int(cds_start):int(cds_end)]

        # Filter by valid cds structure
        if expected_orf_structure is True:
            # Write out
            if (end_cds != 'TAA' and end_cds != 'TGA' and end_cds != 'TAG') and (start_cds != 'ATG'):
                write_b = [tx_information[0], tx_information[1], tx_biotype, cds_start, start_cds, cds_end, end_cds,
                           exon_starting, exon_ending, cds_slice, reference_sequence]
                wr = '\t'.join(write_b)
                wr = wr + '\n'
                tf_out.write(wr)
                continue
            elif (end_cds != 'TAA' and end_cds != 'TGA' and end_cds != 'TAG'):
                write_r = [tx_information[0], tx_information[1], tx_biotype, cds_start, start_cds, cds_end, end_cds,
                           exon_starting, exon_ending, cds_slice, reference_sequence]
                writes = '\t'.join(write_r)
                writes = writes + '\n'
                t_out.write(writes)
                continue
            elif (start_cds != 'ATG'):
                write_l = [tx_information[0], tx_information[1], tx_biotype, cds_start, start_cds, cds_end, end_cds,
                           exon_starting, exon_ending, cds_slice, reference_sequence]
                write = '\t'.join(write_l)
                write = write + '\n'
                f_out.write(write)
                continue
            else:
                pass

    # Write fasta
    fal = ['>' + tx_information[0], tx_information[-3]]
    falo = '\n'.join(fal)
    falo = falo + '\n'
    fasta.write(falo)
    # Protein fasta
    if tx_information[5] is not None:
        if re.match('ENSP', tx_information[5]):
            pal = ['>' + tx_information[5], str(pep_dict[tx_information[5]].seq)]
            palo = '\n'.join(pal)
            palo = palo + '\n'
            fasta.write(palo)
    esl = [tx_information[0], tx_information[8], tx_information[-1], tx_information[3], tx_information[9]]
    eslo = '\t'.join(esl)
    eslo = eslo + '\n'
    exonset.write(eslo)
    # Handle NC transcripts
    if str(tx_information[11]) == '0,0':
        til = [tx_information[-2], tx_information[0], tx_information[1], '', tx_information[-5]]
    else:
        til = [tx_information[-2], tx_information[0], tx_information[1], str(tx_information[-4]), tx_information[-5]]
    tilo = '\t'.join(til)
    tilo = tilo + '\n'
    txinfo.write(tilo)
    asl = [tx_information[1], tx_information[0], tx_information[5], tx_information[-2]]
    try:
        aslo = '\t'.join(asl)
        aslo = aslo + '\n'
        assocacs.write(aslo)
    except TypeError:
        continue

# Close files
fasta.close()
exonset.close()
txinfo.close()
assocacs.close()
t_out.close()
f_out.close()
tf_out.close()

# Record end time
end_time = time.time()
print end_time - start_time
