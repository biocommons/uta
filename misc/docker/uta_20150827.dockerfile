# uta dockerfile -- builds postgresql image with uta_20150827 schema
# PostgreSQL 9.4.4 image with uta_20150827 installed
# https://bitbucket.org/biocommons/uta/"
# 
# Use like this:
# docker build -f uta_20150827.dockerfile --rm=true -t biocommons/uta:uta_20150827 .
# docker run --name uta_20150827 -p 15032:5432 biocommons/uta:uta_20150827 

FROM postgres:9.4.4

RUN apt-get update && apt-get install -y \
    curl

ENV POSTGRES_PASSWORD=password-login-is-disabled

MAINTAINER reecehart@gmail.com
ENV UTA_VERSION=uta_20150827
ENV UTA_PGD_URL=http://dl.biocommons.org/uta-dumps/${UTA_VERSION}-schema.pgd.gz
LABEL description="PostgreSQL 9.4.4 image with $UTA_VERSION installed; https://bitbucket.org/biocommons/uta/"

ADD load-uta.sh /docker-entrypoint-initdb.d/

# postgres entrypoint will run load-uta.sh automatically

