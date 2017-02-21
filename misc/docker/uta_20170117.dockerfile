# uta dockerfile -- https://bitbucket.org/biocommons/uta/
# 
# (Hey, Reece) build like this:
# 1. push dump to minion
# see uta/loading/admin.mk
# 2. build docker image
# docker build -f uta_20170117.dockerfile --rm=true -t biocommons/uta:uta_20170117 .
# 3. test it
# docker run -v /tmp:/tmp --name uta_20170117 -p 10117:5432 biocommons/uta:uta_20170117
# 4. if successful, tag and push
# docker tag biocommons/uta:uta_20170117 biocommons/uta
# docker push biocommons/uta:uta_20170117
# docker push biocommons/uta:latest 

# Then use it:
# docker run --name uta_20170117 -p 10117:5432 biocommons/uta:uta_20170117

# add -e UTA_SCHEMA_ONLY=1 to test by installing the schema only

FROM postgres:9.5

RUN apt-get update && apt-get install -y \
    curl

ENV POSTGRES_PASSWORD=password-login-is-disabled

MAINTAINER reecehart@gmail.com
ENV UTA_VERSION=uta_20170117
LABEL description="PostgreSQL image with $UTA_VERSION installed (https://github.com/biocommons/uta/)"

ADD load-uta.sh /docker-entrypoint-initdb.d/

# postgres entrypoint will run load-uta.sh automatically

