#!/bin/bash

set -e

DOWNLOAD_DIR=$1
DOWNLOAD_PATHS=(
    'gene/DATA/GENE_INFO/Mammalia/Homo_sapiens.gene_info.gz'
    'gene/DATA/gene2accession.gz'
    'refseq/H_sapiens/mRNA_Prot/human.*.rna.gbff.gz'
)

for DOWNLOAD_PATH in "${DOWNLOAD_PATHS[@]}"
do
    # each top-level directory in NCBI is an rsync module.
    # bash parameter expansion removes all content after first slash.
    DOWNLOAD_MODULE="${DOWNLOAD_PATH%%/*}"
    DOWNLOAD_SRC="ftp.ncbi.nlm.nih.gov::$DOWNLOAD_PATH"
    DOWNLOAD_DST="$DOWNLOAD_DIR/$DOWNLOAD_MODULE"
    echo "Downloading $DOWNLOAD_SRC to $DOWNLOAD_DST"
    rsync --no-motd -DHPRprtv "$DOWNLOAD_SRC" "$DOWNLOAD_DST"
done
