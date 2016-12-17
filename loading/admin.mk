############################################################################
#= DB Building and Administration

# dump and push:

# T=uta_20161024
# make -f admin.mk dump-$T
# make -f admin.mk push-dl-$T



SHELL:=/bin/bash -e -o pipefail
PATH:=../sbin:${PATH}



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

#=> restore-from-% -- reconstitute from dump
.PRECIOUS: logs/uta_dev@localhost/restore-from-%.log
restore-from-%: logs/uta_dev@localhost/restore-from-%.log;
logs/uta_dev@localhost/restore-from-%.log: dumps/%.pgd.gz
	@mkdir -pv ${@D}
	(gzip -cdq $< | time psql -h /tmp -U uta_admin -d uta_dev -aeE) >$@.tmp 2>&1 
	mv "$@.tmp" "$@"

#=> dev-from-% -- reconstitute uta_1_1 from dump
.PRECIOUS: logs/uta_dev@localhost/dev-from-%.log
dev-from-%: logs/uta_dev@localhost/dev-from-%.log;
logs/uta_dev@localhost/dev-from-%.log: dumps/%.pgd.gz
	@mkdir -pv ${@D}
	(gzip -cdq $< | pg-dump-schema-rename $* uta_1_1 | time psql -h /tmp -U uta_admin -d uta_dev -aeE) >$@.tmp 2>&1 
	mv "$@.tmp" "$@"


.PRECIOUS: %.sha1
%.sha1: %
	(cd "${<D}"; sha1sum "${<F}") >"$@.tmp"
	/bin/mv "$@.tmp" "$@"



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

