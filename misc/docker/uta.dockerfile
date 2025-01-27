FROM postgres:17

RUN apt-get update && apt-get install -y \
    curl

# docker build --build-arg uta_version=uta_MYVERSION
ARG uta_version=you-did-not-pass-a-build-arg
ARG uta_baseurl=https://dl.biocommons.org/uta

ENV UTA_VERSION=${uta_version}
ENV UTA_BASEURL=${uta_baseurl}
ENV PGDATA=/var/lib/postgresql/data/$UTA_VERSION
LABEL description="PostgreSQL image with $UTA_VERSION installed (https://github.com/biocommons/uta/)"

ADD load-uta.sh /docker-entrypoint-initdb.d/

# postgres entrypoint will run load-uta.sh automatically
