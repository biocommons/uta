#!/bin/bash

# This script is used to upgrade older UTA schemas (specifically uta_20210129b) to a newer version.
# Part of this upgrade is to introduce gene_id to the gene and transcript tables. The columns are
# added with a Alembic migration. Then a data migration to back fill the new columns. Then a second
# Alembic migration to add the constraints to the columns and update primary and foreign keys.

if [ "$#" -lt 1 ]
then
    echo "error: too few arguments, you provided $#, 1 required"
    echo "usage: upgrade-uta-schema.sh <dest_uta_v>"
    exit 1
fi

set -euxo pipefail

source_uta_v="uta_20210129b"
working_uta_v="uta"
dest_uta_v=$1
dumps_dir="/workdir/dumps"
mkdir -p $dumps_dir

## setup working uta schema
# delete schema if exists
psql -h localhost -U uta_admin -d uta -c "DROP SCHEMA IF EXISTS $working_uta_v CASCADE;"

# dump source version
pg_dump -U uta_admin -h localhost -d uta -n "$source_uta_v" | \
 gzip -c > $dumps_dir/"$source_uta_v".pgd.gz

# create new schema
gzip -cdq $dumps_dir/"$source_uta_v".pgd.gz | \
 sbin/pg-dump-schema-rename "$source_uta_v" "$working_uta_v" | \
 sbin/pg-dump-schema-rename "uta_1_1" "$working_uta_v" | \
 psql -U uta_admin -h localhost -d uta -aeE

## upgrade working uta schema
# set initial Alembic migration so it is not ran.
alembic -c etc/alembic.ini stamp edadb97f6502

# run Alembic migration to add gene_id to gene and transcript tables
alembic -c etc/alembic.ini upgrade 595a586e6de7

# run data migration to back fill gene_id
python misc/gene-update/backfill_gene_id.py \
  postgresql://uta_admin:@localhost/uta \
  /workdir/backfill/gene_update.tsv \
  /workdir/backfill/transcript_update.tsv

# run Alembic migrations to add constraints and update existing views
alembic -c etc/alembic.ini upgrade head

## Rename schema to destination schema name
psql -h localhost -U uta_admin -d uta -c "DROP SCHEMA IF EXISTS $dest_uta_v CASCADE;"
psql -h localhost -U uta_admin -d uta -c "ALTER SCHEMA uta RENAME TO $dest_uta_v";
