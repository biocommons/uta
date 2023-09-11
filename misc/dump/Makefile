# Manage releasing a uta schema dump from dev to dl.biocommons.org and to prd


.SUFFIXES:
.PHONY: FORCE
.DELETE_ON_ERROR:

SHELL:=/bin/bash -o pipefail

SCHEMA:=uta_20210129b

export PGUSER=postgres
export PGHOST=uta.biocommons.org

FILES:=${SCHEMA}.pgd.gz	${SCHEMA}-schema.pgd.gz ${SCHEMA}.pgd.gz.sha512 ${SCHEMA}-schema.pgd.gz.sha512  

.PHONY: dumps
dumps: ${FILES}

%-schema.pgd.gz:
	pg_dump -d uta_dev -U uta_admin --no-owner -n $* --schema-only | gzip -cq >$@

%.pgd.gz:
	pg_dump -d uta_dev -U uta_admin --no-owner -n $*               | gzip -cq >$@

%.sha512: %
	sha512sum $< >$@

.PHONY: push
dl-push: ${FILES}
	rsync --progress $^ stuart:/biocommons/dl.biocommons.org/uta/

.PHONY: 
db-push: ${SCHEMA}.pgd.gz
	gzip -cdq <$< | time psql -d uta -1be -v ON_ERROR_STOP=1 -f -
