#!/bin/bash

export uta_v=uta_20210129b

## get the file
rsync --no-motd -HRavP --no-relative  ftp.ncbi.nlm.nih.gov::genomes/refseq/vertebrate_mammalian/Homo_sapiens/all_assembly_versions/GCF_000001405.25_GRCh37.p13/GCF_000001405.25_GRCh37.p13_genomic.gff.gz .


## extract exon alignments
python sbin/ncbi_parse_genomic_gff.py GCF_000001405.25_GRCh37.p13_genomic.gff.gz


### pull a uta database
docker pull biocommons/uta:$uta_v

### stand up container for UTA database
docker run -d -v /tmp:/tmp -v uta_vol:/var/lib/postgresql/data --name $uta_v --network=host biocommons/uta:$uta_v
sleep 5
docker ps

## update the uta database
uta --conf=etc/global.conf --conf=etc/uta_dev@localhost.conf load-exonset ncbi-gff.exonset.gz


## psql_dump
pg_dump -U uta_admin -h localhost -d uta -t uta_20210129b.gene | gzip -c > uta.pgd.gz
## stop local postgres container
docker stop uta_20210129b
docker rm uta_20210129b
