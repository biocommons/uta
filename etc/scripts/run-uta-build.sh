#!/bin/bash

# source_uta_v is the UTA version before the update.
# seqrepo_data_release is the SeqRepo version before the update.
# ncbi_dir is where the script looks for NCBI data files.
# working_dir stores log files, intermediate data files, and the final database dump.

set -euxo pipefail

source_uta_v=$1
seqrepo_data_release=$2
ncbi_dir=$3
working_dir=$4

if [ -z "$source_uta_v" ] || [ -z "$seqrepo_data_release" ] || [ -z "$ncbi_dir" ] || [ -z "$working_dir" ]
then
    echo 'Usage: run-uta-build.sh <source_uta_v> <seqrepo_data_release> <ncbi_dir> <working_dir>'
    exit 1
fi

# set local variables and create working directories
loading_uta_v="uta_1_1"
loading_dir="$working_dir/loading"
dumps_dir="$working_dir/dumps"
logs_dir="$working_dir/logs"
for d in "$loading_dir" "$dumps_dir" "$logs_dir";
  do mkdir -p "$d"
done

## Drop loading schema, and recreate
etc/scripts/delete-schema.sh "$loading_uta_v"
etc/scripts/create-new-schema.sh "$source_uta_v" "$loading_uta_v"

## Load SeqRepo with new sequences
seqrepo load -n NCBI -i "$seqrepo_data_release" \
  $ncbi_dir/refseq/H_sapiens/mRNA_Prot/human.*.rna.fna.gz \
  $ncbi_dir/refseq/H_sapiens/mRNA_Prot/human.*.protein.faa.gz \
  $ncbi_dir/genomes/refseq/vertebrate_mammalian/Homo_sapiens/all_assembly_versions/GCF_000001405*/GCF_*_genomic.fna.gz 2>& 1 | \
  tee "$logs_dir/seqrepo-load.log"

### extract meta data
# genes
sbin/ncbi-parse-geneinfo $ncbi_dir/gene/DATA/GENE_INFO/Mammalia/Homo_sapiens.gene_info.gz | \
  gzip -c > "$loading_dir/genes.geneinfo.gz" 2>&1 | tee "$logs_dir/ncbi-parse-geneinfo.log"

# transcript protein associations
sbin/ncbi-parse-gene2refseq $ncbi_dir/gene/DATA/gene2accession.gz | gzip -c > "$loading_dir/assocacs.gz" 2>&1 | \
  tee "$logs_dir/ncbi-fetch-assoc-acs"

# parse transcript info from GBFF input files
GBFF_files=$(ls $ncbi_dir/refseq/H_sapiens/mRNA_Prot/human.*.rna.gbff.gz)
sbin/ncbi-parse-gbff "$GBFF_files" | gzip -c > "$loading_dir/gbff.txinfo.gz" 2>&1 | \
  tee "$logs_dir/ncbi-parse-gbff.log"

# parse alignments from GFF input files
GFF_files=$(ls $ncbi_dir/genomes/refseq/vertebrate_mammalian/Homo_sapiens/all_assembly_versions/GCF_000001405*/GCF_*_genomic.gff.gz)
sbin/ncbi_parse_genomic_gff.py "$GFF_files" | gzip -c > "$loading_dir/gff.exonsets.gz" 2>&1 | \
  tee "$logs_dir/ncbi-parse-genomic-gff.log"

# generate seqinfo files from exonsets
sbin/exonset-to-seqinfo -o NCBI "$loading_dir/gff.exonsets.gz" | gzip -c > "$loading_dir/seqinfo.gz" 2>&1 | \
  tee "$logs_dir/exonset-to-seqinfo.log"


### update the uta database
# genes
uta --conf=etc/global.conf --conf=etc/uta_dev@localhost.conf load-geneinfo "$loading_dir/genes.geneinfo.gz" 2>&1 | \
  tee "$logs_dir/load-geneinfo.log"

# transcript info
uta --conf=etc/global.conf --conf=etc/uta_dev@localhost.conf load-txinfo "$loading_dir/gbff.txinfo.gz" 2>&1 | \
  tee "$logs_dir/load-txinfo.log"

# gff exon sets
uta --conf=etc/global.conf --conf=etc/uta_dev@localhost.conf load-exonset "$loading_dir/gff.exonsets.gz" 2>&1 | \
  tee "$logs_dir/load-exonsets.log"

# align exons
#uta --conf=etc/global.conf --conf=etc/uta_dev@localhost.conf align-exons 2>&1 | tee "$logs_dir/align-exons.log"


### run diff
sbin/uta-diff "$source_uta_v" "$loading_uta_v"


### psql_dump
pg_dump -U uta_admin -h localhost -d uta -t "$loading_uta_v.gene" | gzip -c > "$dumps_dir/uta.pgd.gz"
