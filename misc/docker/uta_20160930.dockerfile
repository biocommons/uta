# uta dockerfile -- https://bitbucket.org/biocommons/uta/
# 
# Use like this:
# docker build -f uta_20160930.dockerfile --rm=true -t biocommons/uta:uta_20160930 .
# docker tag biocommons/uta:uta_20160930 biocommons/uta
# docker run --name uta_20160930 -p 60930:5432 biocommons/uta:uta_20160930
# docker push biocommons/uta:uta_20160930
# docker push biocommons/uta:latest 
#
# add -e UTA_SCHEMA_ONLY=1 to test by installing the schema only

FROM postgres:9.5

RUN apt-get update && apt-get install -y \
    curl

ENV POSTGRES_PASSWORD=password-login-is-disabled

MAINTAINER reecehart@gmail.com
ENV UTA_VERSION=uta_20160930
LABEL description="PostgreSQL image with $UTA_VERSION installed (https://github.com/biocommons/uta/)"

ADD load-uta.sh /docker-entrypoint-initdb.d/

# postgres entrypoint will run load-uta.sh automatically

