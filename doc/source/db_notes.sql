#restore database
gzip -cdq dumps/uta_20150702.pgd.gz | psql -h uta.biocommons.org -U uta_admin -d uta_dev -aeE


../sbin/pg-dump-schema-rename $existing_schema_name $new_schema_name \
| psql -U postgres -d uta_dev
