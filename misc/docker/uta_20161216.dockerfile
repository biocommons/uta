# uta dockerfile -- https://bitbucket.org/biocommons/uta/
# 
# Build like this:
# docker build -f uta_20161216.dockerfile --rm=true -t biocommons/uta:uta_20161216 .
# docker tag biocommons/uta:uta_20161216 biocommons/uta
# docker push biocommons/uta:uta_20161216
# docker push biocommons/uta:latest 

# Then use it:
# docker run --name uta_20161216 -p 61216:5432 biocommons/uta:uta_20161216

# add -e UTA_SCHEMA_ONLY=1 to test by installing the schema only

FROM postgres:9.5

RUN apt-get update && apt-get install -y \
    curl

ENV POSTGRES_PASSWORD=password-login-is-disabled

MAINTAINER reecehart@gmail.com
ENV UTA_VERSION=uta_20161216
LABEL description="PostgreSQL image with $UTA_VERSION installed (https://github.com/biocommons/uta/)"

ADD load-uta.sh /docker-entrypoint-initdb.d/

# postgres entrypoint will run load-uta.sh automatically

