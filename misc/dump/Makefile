.SUFFIXES:
.PHONY: FORCE
.DELETE_ON_ERROR:

SHELL:=/bin/bash -o pipefail

SCHEMA:=uta_20140210

export PGUSER=reece
export PGDATABASE=reece
export PGHOST=


default: ${SCHEMA}-schema.pgd.gz ${SCHEMA}-schema.pgd.gz.sha1 ${SCHEMA}.pgd.gz ${SCHEMA}.pgd.gz.sha1


%-schema.pgd.gz:
	pg_dump -U uta_admin --no-owner -n $* --schema-only | gzip -cq >$@

%.pgd.gz:
	pg_dump -U uta_admin --no-owner -n $*               | gzip -cq >$@

%.sha1: %
	sha1sum $< >$@


uta-push-%: %.pgd.gz
	gzip -cdq <$< | time psql -1 -v ON_ERROR_STOP=1 -h uta.invitae.com -U uta_admin -d uta -f -

db-push-%: %.pgd.gz
	gzip -cdq <$< | time psql -1 -v ON_ERROR_STOP=1 -h db.locusdev.net -U reece -d uta -f -
