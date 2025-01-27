#!/bin/bash -eux
# This file creates a password-less read-only instance of UTA
# (https://github.com/biocommons/uta/) based on the postgres docker
# image.

# TODO:
# * fetch sha1 and check before loading

# Overwrite pg_hba.conf, including whatever edits might have been made
# by the postgres image
cat <<EOF >"$PGDATA/pg_hba.conf"
# allow the anonymous user to access uta without password
# These lines must occur before more stringent authentication methods
host   all   anonymous     0.0.0.0/0      trust
host   all   PUBLIC        0.0.0.0/0      trust
local  all   all                          trust
host   all   all         127.0.0.1/32     trust
host   all   all               ::1/128    trust
EOF


# Create required users
createuser --username "$POSTGRES_USER" uta_admin
createuser --username "$POSTGRES_USER" uta_public
createuser --username "$POSTGRES_USER" anonymous
createuser --username "$POSTGRES_USER" PUBLIC
createdb   --username "$POSTGRES_USER" -O uta_admin uta

# Stream db dump into psql
# When the image is first run, the output from curl and psql are
# comingled.  This is intentional so that the user can see curl
# progress and pg restore progress.

UTA_BASENAME=${UTA_VERSION}${UTA_SCHEMA_ONLY:+-schema}.pgd.gz
UTA_PGD_URL=${UTA_BASEURL}/${UTA_BASENAME}
UTA_PGD_FN=/tmp/${UTA_BASENAME}

if ! [ -e "${UTA_PGD_FN}" ]; then
    curl -o "${UTA_PGD_FN}.tmp" "$UTA_PGD_URL"
    mv "${UTA_PGD_FN}.tmp" "${UTA_PGD_FN}"
fi

gzip -cdq < "${UTA_PGD_FN}" \
    | psql -1e -U uta_admin -d uta -v ON_ERROR_STOP=1


psql -1e -U uta_admin -d uta -v ON_ERROR_STOP=1 <<EOF
ALTER DATABASE :DBNAME SET search_path=$UTA_VERSION
EOF


cat <<EOF
=======================================================================
=======================================================================
==
== $UTA_VERSION installed from
== $UTA_PGD_URL
==
== You may now connect to uta like this:
==
== $  psql -h localhost -p <port> -U anonymous -d uta
==
== No password is required.
==
=======================================================================
=======================================================================

EOF


date >/tmp/uta-ready
