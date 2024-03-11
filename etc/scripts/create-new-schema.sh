#!/bin/bash

if [ "$#" -lt 2 ]
then
    echo "error: too few arguments, you provided $#, 1 required"
    echo "usage: create-new-schema.sh <source_uta_v>"
    exit 1
fi

set -euxo pipefail

source_uta_v=$1
dest_uta_v=$2
dumps_dir=/temp/dumps
mkdir -p $dumps_dir

# dump current version
pg_dump -U uta_admin -h localhost -d uta -n "$source_uta_v" | \
 gzip -c > $dumps_dir/"$source_uta_v".pgd.gz

# create new schema
gzip -cdq $dumps_dir/"$source_uta_v".pgd.gz | \
 sbin/pg-dump-schema-rename "$source_uta_v" "$dest_uta_v" | \
 psql -U uta_admin -h localhost -d uta -aeE
