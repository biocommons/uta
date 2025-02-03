# Developer Notes

## Command lines

    sudo service postgresql start # or stop

    export PGPASSWORD=...

    # load postgresql from dump
    psql \
        -h localhost -U uta_admin -d uta_dev \
        -v ON_ERROR_STOP=1 -1 -Eae \
        -f <(gzip -cdq uta_20240523b.pgd.gz) \
        >|load.log 2>|load.err &

    # extract words before schema names in schema dump
    pg_dump postgresql://uta_admin@localhost/uta_dev -n uta_20240523b -s \
    | perl -lne 'print $1 while m/([A-Z][\sA-Z]+uta_20240523b)/gms' \
    | sort -u \
    | perl -pe 's/^(.+)\s+uta_20240523b/"$1",/'

    # generate diff stats between two uta schemas (as markdown)
    ./sbin/uta-diff uta_20240523b uta_20241220 >|uta_20241220.md

