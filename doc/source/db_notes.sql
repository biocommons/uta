#dump database:
pg_dump -h uta.biocommons.org -U ivpostgres -d $d | gzip -c >|$d.pgd.gz

# create database

#restore database
gzip -cdq dumps/uta_20150702.pgd.gz | psql -h uta.biocommons.org -U uta_admin -d uta_dev -aeE
