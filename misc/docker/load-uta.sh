#!/bin/bash -x

# postgres is already started for running entry point scripts,
# so this won't take effect until restart

cat <<EOF >/tmp/trust-block

# allow the anonymous user to access uta without password
# These lines must occur before more stringent authentication methods
local  all   anonymous                trust
host   all   anonymous   0.0.0.0/0    trust
EOF

cp "$PGDATA/pg_hba.conf"  "$PGDATA/pg_hba.conf.orig" 
sed '/^# TYPE/ r /tmp/trust-block' "$PGDATA/pg_hba.conf.orig" > "$PGDATA/pg_hba.conf" 


createuser --username "$POSTGRES_USER" uta_admin
createuser --username "$POSTGRES_USER" anonymous
createdb   --username "$POSTGRES_USER" -O uta_admin uta


curl "$UTA_PGD_URL" \
    | gzip -cdq \
    | psql -1e -U uta_admin -d uta -v ON_ERROR_STOP=1

cat <<EOF
=======================================================================
=======================================================================
== 
== $UTA_VERSION installed
== 
== You may now connect to uta. 
== 
== Reminder: Your password is '$POSTGRES_PASSWORD'. If you didn't set it,
== consider doing so with 
==    docker run ... -e POSTGRES_PASSWORD=your_password
== 
=======================================================================
=======================================================================

EOF


cat $PGDATA/pg_hba.conf
