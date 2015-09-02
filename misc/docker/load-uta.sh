#!/bin/sh -x

gosu postgres createuser uta_admin
gosu postgres createuser anonymous
gosu postgres createdb -O uta_admin uta

curl "$UTA_PGD_URL" \
    | gzip -cdq \
    | psql -U uta_admin -d uta -aeE
