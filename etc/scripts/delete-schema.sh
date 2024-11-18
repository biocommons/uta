#!/bin/bash

if [ "$#" -lt 1 ]
then
    echo "error: too few arguments, you provided $#, 1 required"
    echo "usage: delete-schema.sh <source_uta_v>"
    exit 1
fi

set -euxo pipefail

source_uta_v=$1

psql -h localhost -U uta_admin -d uta -c "DROP SCHEMA IF EXISTS $source_uta_v CASCADE"