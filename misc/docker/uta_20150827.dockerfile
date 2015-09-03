# uta dockerfile -- builds postgresql image with uta_20150827 schema
# PostgreSQL 9.4.4 image with uta_20150827 installed
# https://bitbucket.org/biocommons/uta/"
# 
# Use like this:
# docker build -f uta_20150827.dockerfile --rm=true -t biocommons/uta:20150827 .
# docker run -p 15032:5432 uta_20150827.dockerfile

FROM postgres:9.4.4

ENV UTA_VERSION=uta_20150827
ENV UTA_PGD_URL=http://dl.biocommons.org/uta-dumps/${UTA_VERSION}-schema.pgd.gz

LABEL description="PostgreSQL 9.4.4 image with $UTA_VERSION installed; https://bitbucket.org/biocommons/uta/"
MAINTAINER reecehart@gmail.com

RUN apt-get update && apt-get install -y \
    curl

ADD load-uta.sh /docker-entrypoint-initdb.d/

# postgres entrypoint will run load-uta.sh automatically

