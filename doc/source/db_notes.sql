#dump database:
pg_dump -h uta.biocommons.org -U ivpostgres -d $d | gzip -c >|$d.pgd.gz

# create database

#restore database
gzip -cdq dumps/uta_20150702.pgd.gz | psql -h uta.biocommons.org -U uta_admin -d uta_dev -aeE


createdb -h uta.invitae.com -U ivpostgres -O uta_admin   uta_dev

# copy schema to uta.biocommons.org
pg_dump -d uta_dev -n uta_20150729 | psql -h uta.biocommons.org -U uta_admin -d uta_dev

# copy schema in a database with renaming
existing_schema_name=uta_20150704
new_schema_name=uta_20150729
pg_dump -U postgres -d uta_dev -n $existing_schema_name \
| ../sbin/pg-dump-schema-rename $existing_schema_name $new_schema_name \
| psql -U postgres -d uta_dev
