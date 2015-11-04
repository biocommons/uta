# uta dockerfile -- builds postgresql image with uta_20150903 schema
# PostgreSQL 9.4.4 image with uta_20150903 installed
# https://bitbucket.org/biocommons/uta/"
# 
# Use like this:
# docker build -f uta_20150903.dockerfile --rm=true -t biocommons/uta:uta_20150903 .
# docker run --name uta_20150903 -p 15032:5432 biocommons/uta:uta_20150903 
# add -e UTA_SCHEMA_ONLY=1 to test by installing the schema only

FROM postgres:9.4.5

RUN apt-get update && apt-get install -y \
    curl

ENV POSTGRES_PASSWORD=password-login-is-disabled

MAINTAINER reecehart@gmail.com
ENV UTA_VERSION=uta_20150903
LABEL description="PostgreSQL image with $UTA_VERSION installed (https://bitbucket.org/biocommons/uta/)"

ADD load-uta.sh /docker-entrypoint-initdb.d/

# postgres entrypoint will run load-uta.sh automatically

