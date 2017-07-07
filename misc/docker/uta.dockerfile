FROM postgres:9.6

RUN apt-get update && apt-get install -y \
    curl

ENV POSTGRES_PASSWORD=password-login-is-disabled

# by default we are using uta_20170707
# please provide custom versions with the command line parameter
# --build-arg uta_version=uta_MYVERSION
ARG uta_version=uta_201700707

MAINTAINER reecehart@gmail.com
ENV UTA_VERSION=${uta_version}
LABEL description="PostgreSQL image with $UTA_VERSION installed (https://github.com/biocommons/uta/)"

ADD load-uta.sh /docker-entrypoint-initdb.d/

# postgres entrypoint will run load-uta.sh automatically

