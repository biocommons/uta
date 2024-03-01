#!/bin/bash

export uta_v=uta_20210129b

## get the file
rsync --no-motd -HRavP ftp.ncbi.nlm.nih.gov::gene/DATA/GENE_INFO/Mammalia/Homo_sapiens.gene_info.gz .

## extract meta data
sbin/ncbi-parse-geneinfo DATA/GENE_INFO/Mammalia/Homo_sapiens.gene_info.gz | gzip -c > genes.geneinfo.gz

### pull a uta database
docker pull biocommons/uta:$uta_v

### stand up container for UTA database
docker run -d -v /tmp:/tmp -v uta_vol:/var/lib/postgresql/data --name $uta_v --network=host biocommons/uta:$uta_v
sleep 5
docker ps

## update the uta database
uta --conf=etc/global.conf --conf=etc/uta_dev@localhost.conf load-geneinfo genes.sample.gz

## psql_dump
pg_dump -U uta_admin -h localhost -d uta -t uta_20210129b.gene | gzip -c > uta.pgd.gz
## stop local postgres container
docker stop uta_20210129b
docker rm uta_20210129b
