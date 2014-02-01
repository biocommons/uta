.SUFFIXES :
.PRECIOUS :
.PHONY : FORCE
.DELETE_ON_ERROR:

SHELL:=/bin/bash -o pipefail
PATH:=../sbin:${PATH}
SELF:=$(firstword $(MAKEFILE_LIST))


############################################################################
#= BASIC USAGE
default: help

#=> help -- display this help message
help:
	@extract-makefile-documentation "${SELF}"



data/ncbi.exonsets.gz data/ncbi.geneinfo.gz data/ncbi.txinfo.gz: data/ncbi.log;
data/ncbi.log: %.log: data/genes.hgnc.gz
	{ gzip -cdq <$< | ncbi-fetch -p $* 2>&1 | tee $@.tmp; } && mv -v $@.tmp $@

data/ucsc.exonsets.gz:
	ucsc-fetch-exonsets && mv ucsc.exonsets.gz data/



############################################################################
## test data

TEST_CONF=test.conf
include .${TEST_CONF}
.${TEST_CONF}: ${TEST_CONF}
	../sbin/conf-to-vars $< >$@

#=> testdb -- create a test database with small input
testdb: test-data/ncbi.geneinfo.gz test-data/ncbi.txinfo.gz test-data/ncbi.exonsets.gz
	# >>> if ${uta_database} already exists, we'll ignore that error
	-createdb ${uta_database}
	uta --conf=${TEST_CONF} drop-schema
	uta --conf=${TEST_CONF} create-schema
	uta --conf=${TEST_CONF} create-views ../sql/views.sql
	uta --conf=${TEST_CONF} initialize-schema
	uta --conf=${TEST_CONF} load-geneinfo $(word 1,$^)
	uta --conf=${TEST_CONF} load-txinfo $(word 2,$^)
	uta --conf=${TEST_CONF} load-exonsets $(word 3,$^)
	uta --conf=${TEST_CONF} align-exons /locus/data/core-rest/2014-01/sequences/


test-data/ncbi.exonsets.gz: data/ncbi.exonsets.gz
	gzip -cdq <$< | perl -ne 'print if $$.==1 or m/^(?:NM_000039.1|NM_000040.1|NM_000041.2|NM_000055.2)\s/' | gzip -cq >$@
test-data/ncbi.geneinfo.gz: data/ncbi.geneinfo.gz
	gzip -cdq <$< | perl -ne 'print if $$.==1 or m/^(?:APOC3|BCHE|APOE|APOA1)\s/' | gzip -cq >$@
test-data/ncbi.txinfo.gz: data/ncbi.txinfo.gz
	gzip -cdq <$< | perl -aF'\t' -ne 'print if $$.==1 or $$F[1] =~ m/^(?:NM_000039.1|NM_000040.1|NM_000041.2|NM_000055.2)$$/' | gzip -cq >$@



#=> setup-perl: install perl packages
# TODO: consider perl brew instead
setup-perl:
	./sbin/perl-module-install --install-base ve   Log::Log4perl


############################################################################
#= CLEANUP
.PHONY: clean cleaner cleanest pristine
#=> clean: clean up editor backups, etc.
clean:
	find . -name \*~ -print0 | xargs -0r /bin/rm
#=> cleaner: above, and remove generated files
cleaner: clean
	find . -name \*.pyc -print0 | xargs -0r /bin/rm -f
	/bin/rm -fr distribute-* *.egg *.egg-info *.tar.gz nosetests.xml
	/bin/rm -fr .uta.conf.mk
	make -C doc clean
#=> cleanest: above, and remove the virtualenv, .orig, and .bak files
cleanest: cleaner
	find . \( -name \*.orig -o -name \*.bak \) -print0 | xargs -0r /bin/rm -v
	/bin/rm -fr build bdist dist sdist ve virtualenv*
#=> pristine: above, and delete anything unknown to mercurial
pristine: cleanest
	# deleting anything unknown to mercurial, including your
	# precious uncommitted changes
	hg st -un0 | xargs -0r echo /bin/rm -fv
