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
## testdb

TEST_CONF=test.conf
include .${TEST_CONF}
.${TEST_CONF}: ${TEST_CONF}
	../sbin/conf-to-vars $< >$@

#=> test-data -- build test data (currently 4 genes, 4 transcripts)
.PHONY: test-data
test-data: test-data/ncbi.geneinfo.gz test-data/ncbi.txinfo.gz test-data/ncbi.exonsets.gz;


# select one gene,ac combo for 3-exon transcript with each status,strand possibility
# uta=# select distinct on (status,strand) status,strand,gene,ac from transcript_table_mv where gene !~ 'orf|BEAN1' and n_t_exons=3;
#  status | strand |  gene   |       ac       
# --------+--------+---------+----------------
#  nlxdi  |     -1 | VSX1    | NM_001256271.1
#  nlXDI  |     -1 | KCNJ8   | NM_004982.2
#  NlxdI  |     -1 | GPHB5   | NM_145171.3
#  NlxdI  |      1 | GFER    | NM_005262.2
#  NlxDi  |     -1 | ZNF787  | NM_001002836.2
#  NlxDi  |      1 | TGIF2   | NM_001199513.1
#  NlXdI  |     -1 | CYP1B1  | NM_000104.3
#  NlXDi  |     -1 | EGR2    | NM_001136179.1
#  NLxdi  |     -1 | TMEM86B | NM_173804.4
#  NLxdi  |      1 | RPLP1   | NM_213725.1
#  NLXdi  |     -1 | FUT3    | NM_001097639.1
#  NLXdi  |      1 | KLHL42  | NM_020782.1

test-data/ncbi.geneinfo.gz: data/ncbi.geneinfo.gz test-data/genes
	gzip -cdq <$< \
	| perl -n -e 'BEGIN{open(F,"$(word 2,$^)"); $$re=join("|",map {chomp;$$_} <F>); print(STDERR "re=$$re\n");}' \
		-e 'print if $$.==1 or m/^(?:$$re)\s/' \
	| gzip -cq >$@
	printf "%d $@\n" $$(gzip -cdq <$@ | wc -l)
test-data/ncbi.exonsets.gz: data/ncbi.exonsets.gz test-data/acs
	gzip -cdq <$< \
	| perl -n -e 'BEGIN{open(F,"$(word 2,$^)"); $$re=join("|",map {chomp;$$_} <F>); print(STDERR "re=$$re\n");}' \
		-e 'print if $$.==1 or m/^(?:$$re)\s/' \
	| gzip -cq >$@
	@printf "%d $@\n" $$(gzip -cdq <$@ | wc -l)
test-data/ncbi.txinfo.gz: data/ncbi.txinfo.gz test-data/acs
	gzip -cdq <$< \
	| perl -aF'\t' -ne 'BEGIN{open(F,"$(word 2,$^)"); $$re=join("|",map {chomp;$$_} <F>); print(STDERR "re=$$re\n");}' \
		-e 'print if $$.==1 or $$F[1] =~ m/^(?:$$re)$$/' \
	| gzip -cq >$@
	@printf "%d $@\n" $$(gzip -cdq <$@ | wc -l)

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
