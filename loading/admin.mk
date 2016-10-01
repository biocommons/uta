############################################################################
#= DB Building and Administration

SHELL:=/bin/bash -e -o pipefail
PATH:=../sbin:${PATH}

#=> drop -- 
drop:
	uta ${CONF_OPTS} drop-schema

#=> create -- 
create:
	uta ${CONF_OPTS} create-schema
	uta ${CONF_OPTS} load-sql \
		../sql/internal-views.sql \
		../sql/views.sql \
		../sql/associated_accessions.sql
	uta ${CONF_OPTS} grant-permissions





_mega:
	if [ "${_UTA_MK_ANEW}" = "1" ]; then make drop create migrate-${schema}; fi
	make cleanest 
	make load-origin
	make load-ncbi-associated-accessions
	make ${_UTA_MK_DATASETS}
	make align-exons
	make refresh-matviews

happy-meal:
	make _mega _UTA_MK_ANEW=0 _UTA_MK_DATASETS="load-ncbi/{refmismatch,acmg-mr} load-ensembl-79/{refmismatch,acmg-mr} load-ucsc-hg19"

# full data load, layered on whatever's already in uta_1_1
cheeseburger-royale:
	make _mega _UTA_MK_ANEW=0 _UTA_MK_DATASETS="load-ncbi load-ensembl-79 load-ucsc-hg19"

the-whole-kielbasa:
	make _mega _UTA_MK_ANEW=1 _UTA_MK_DATASETS="load-ncbi load-ensembl-79 load-ucsc-hg19"




#=> dump-% -- dump named schema (e.g., uta_20140210) in dumps/ and compute sha1
dump-%: dumps/%.pgd.gz dumps/%.pgd.gz.sha1 dumps/%-schema.pgd.gz dumps/%-schema.pgd.gz.sha1 ;

#=> dumps/%.pgd.gz -- create dump of named schema (e.g., uta_20140210)
.PRECIOUS: dumps/%.pgd.gz
dumps/%.pgd.gz:
	# expect ~5 minutes
	(time pg_dump -U uta_admin -h localhost -d uta_dev -n $* | gzip) >$@.tmp 2>$@.log
	mv "$@.tmp" "$@"

#=> dumps/%-schema.pgd.gz -- create dump of named schema wo/data (e.g., uta_20140210)
.PRECIOUS: dumps/%-schema.pgd.gz
dumps/%-schema.pgd.gz:
	(time pg_dump -U uta_admin -h localhost -d uta_dev -n $* -s | gzip) >$@.tmp 2>$@.log
	mv "$@.tmp" "$@"

#=> push-% -- push schemas to AWS RDS
push-dl-%: logs/push-dl-%.log;
push-dev-%: logs/uta.biocommons.org/uta_dev/load-%.log;
push-prd-%: logs/uta.biocommons.org/uta/load-%.log;

.PRECIOUS: logs/push-dl-%.log
logs/push-dl-%.log: dumps/%.pgd.gz dumps/%.pgd.gz.sha1 dumps/%-schema.pgd.gz dumps/%-schema.pgd.gz.sha1
	rsync -P $^ minion:dl.biocommons.org/uta/
	touch $@

.PRECIOUS: logs/uta.biocommons.org/uta_dev/load-%.log
logs/uta.biocommons.org/uta_dev/load-%.log: dumps/%.pgd.gz
	# expect 15-90 minutes dep on network
	@mkdir -pv ${@D}
	(gzip -cdq $< | time psql -h uta.biocommons.org -U uta_admin -d uta_dev -aeE) >$@.tmp 2>&1 
	mv "$@.tmp" "$@"
.PRECIOUS: logs/uta.biocommons.org/uta/load-%.log
logs/uta.biocommons.org/uta/load-%.log: dumps/%.pgd.gz
	# expect 15-90 minutes dep on network
	@mkdir -pv ${@D}
	(gzip -cdq $< | time psql -h uta.biocommons.org -U uta_admin -d uta -aeE) >$@.tmp 2>&1 
	mv "$@.tmp" "$@"



#=> dev-from-% -- reconstitute uta_1_1 from dump
dev-from-%: logs/uta_dev@localhost/dev-from-%.log;
logs/uta_dev@localhost/dev-from-%.log: dumps/%.pgd.gz
	@mkdir -pv ${@D}
	(gzip -cdq $< | pg-dump-schema-rename $* uta_1_1 | time psql -h /tmp -U uta_admin -d uta_dev -aeE) >$@.tmp 2>&1 
	mv "$@.tmp" "$@"



############################################################################
#= CLEANUP
.PHONY: clean cleaner cleanest pristine
#=> clean: clean up editor backups, etc.
clean:
	/bin/rm -f *~ *.bak *.tmp
#=> cleaner: above, and remove generated files
cleaner: clean
	/bin/rm -f .*.mk
#=> cleanest: above, and remove the virtualenv, .orig, and .bak files
cleanest: cleaner
	/bin/rm -fr logs


.PRECIOUS: %.sha1
%.sha1: %
	(cd "${<D}"; sha1sum "${<F}") >"$@.tmp"
	/bin/mv "$@.tmp" "$@"

