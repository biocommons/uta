#!/bin/bash

if [ "$#" -lt 2 ]
then
    echo "error : too few arguments, you provided $#, 2 required"
    echo "usage: run_uta_build_gene.sh <source_uta_v> <seqrepo_data_release>"
    exit 1
fi
source_uta_v=$1
seqrepo_data_release=$2

set -euxo pipefail

# set local variables and create working directories
loading_uta_v="uta_1_1"
loading_dir="/temp/loading"
dumps_dir="/temp/dumps"
logs_dir="/temp/logs"
for d in "$loading_dir" "$dumps_dir" "$logs_dir";
  do mkdir -p "$d"
done

## Drop loading schema, and recreate
etc/scripts/delete-schema.sh "$loading_uta_v"
etc/scripts/create-new-schema.sh "$source_uta_v" "$loading_uta_v"

## Load SeqRepo with new sequences
seqrepo load -n NCBI -i "$seqrepo_data_release" \
  /temp/refseq/H_sapiens/mRNA_Prot/human.*.rna.fna.gz \
  /temp/refseq/H_sapiens/mRNA_Prot/human.*.protein.faa.gz \
  /temp/genomes/refseq/vertebrate_mammalian/Homo_sapiens/all_assembly_versions/GCF_000001405*/GCF_*_genomic.fna.gz 2>& 1 | \
  tee "$logs_dir/seqrepo-load.log"

### extract meta data
# genes
sbin/ncbi-parse-geneinfo /temp/gene/DATA/GENE_INFO/Mammalia/Homo_sapiens.gene_info.gz | \
  gzip -c > "$loading_dir/genes.geneinfo.gz" 2>&1 | tee "$logs_dir/ncbi-parse-geneinfo.log"

# transcript protein associations
sbin/ncbi-parse-gene2refseq /temp/gene/DATA/gene2accession.gz | gzip -c > "$loading_dir/assocacs.gz" 2>&1 | \
  tee "$logs_dir/ncbi-fetch-assoc-acs"

# parse transcript info from GBFF input files
GBFF_files=$(ls /temp/refseq/H_sapiens/mRNA_Prot/human.*.rna.gbff.gz)
sbin/ncbi-parse-gbff "$GBFF_files" | gzip -c > "$loading_dir/gbff.txinfo.gz" 2>&1 | \
  tee "$logs_dir/ncbi-parse-gbff.log"


### update the uta database
# genes
uta --conf=etc/global.conf --conf=etc/uta_dev@localhost.conf load-geneinfo "$loading_dir/genes.geneinfo.gz" 2>&1 | \
  tee "$logs_dir/load-geneinfo.log"

# transcript info
uta --conf=etc/global.conf --conf=etc/uta_dev@localhost.conf load-txinfo "$loading_dir/gbff.txinfo.gz" 2>&1 | \
  tee "$logs_dir/load-txinfo.log"


### run diff
sbin/uta-diff "$source_uta_v" "$loading_uta_v"


### psql_dump
pg_dump -U uta_admin -h localhost -d uta -t "$loading_uta_v.gene" | gzip -c > "$dumps_dir/uta.pgd.gz"
