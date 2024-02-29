#!/bin/bash

export uta_v=uta_20210129b

## get the file
rsync --no-motd -HRavP ftp.ncbi.nlm.nih.gov::gene/DATA/GENE_INFO/Mammalia/Homo_sapiens.gene_info.gz .

## extract meta data
sbin/ncbi-parse-geneinfo DATA/GENE_INFO/Mammalia/Homo_sapiens.gene_info.gz | gzip -c > genes.geneinfo.gz

### pull a uta database
docker pull biocommons/uta:$uta_v

### stand up container for UTA database
docker run \
   -d \
   -e POSTGRES_PASSWORD=temp \
   -v /tmp:/tmp \
   -v uta_vol:/var/lib/postgresql/data \
#   -p 5432:5432 \
   --name $uta_v \
   --network=host \
   biocommons/uta:$uta_v

docker ps -a

## update the uta database
uta --conf=etc/global.conf --conf=etc/uta_dev@localhost.conf load-geneinfo genes.geneinfo.gz

## psql_dump

## stop local postgres container
docker stop uta_20210129b
docker rm uta_20210129b
