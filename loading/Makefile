.SUFFIXES :
.PRECIOUS :
.PHONY : FORCE
.DELETE_ON_ERROR:

SHELL:=/bin/bash -o pipefail
PATH:=../sbin:${PATH}
SELF:=$(firstword $(MAKEFILE_LIST))

# move the following to conf
SEQ_DIR:=/locus/data/core-rest/2014-01/sequences

# Instance name
IN=test

DATA_DIR:=${IN}
CONF_FN=${IN}.conf
include .${CONF_FN}
.${CONF_FN}: ${CONF_FN}
	../sbin/conf-to-vars $< >$@

#test-data/ncbi.seqinfo.gz /dev/null test-data/ncbi.geneinfo.gz test-data/ncbi.txinfo.gz test-data/ncbi.exonsets.gz test-data/ucsc.exonsets.gz


############################################################################
#= BASIC USAGE
default: help

#=> help -- display this help message
help:
	@extract-makefile-documentation "${SELF}"


############################################################################
#=> build -- 
build:
	# >>> if ${uta_database} already exists, we'll ignore that error
	-createdb ${uta_database}
	uta --conf=${CONF_FN} drop-schema
	uta --conf=${CONF_FN} create-schema
	uta --conf=${CONF_FN} create-views ../sql/views.sql
	uta --conf=${CONF_FN} initialize-schema
	for f in ${DATA_DIR}/*.seqinfo.gz; do uta --conf=${CONF_FN} load-seqinfo "$$f"; done
	for f in ${DATA_DIR}/*.geneinfo.gz; do uta --conf=${CONF_FN} load-geneinfo "$$f"; done
	for f in ${DATA_DIR}/*.txinfo.gz; do uta --conf=${CONF_FN} load-txinfo "$$f"; done
	for f in ${DATA_DIR}/*.exonsets.gz; do uta --conf=${CONF_FN} load-exonsets "$$f"; done
	uta --conf=${CONF_FN} align-exons ${SEQ_DIR}


############################################################################
## build primary data

data/ensembl.seqinfo.gz: data/ensembl.fasta.gz
	fasta-to-seqinfo -o ensembl $< | gzip -cq >$@

data/ncbi.seqinfo.gz:
	fasta-to-seqinfo -o 'NCBI RefSeq' ${SEQ_DIR}/{hs_*.fa,refseq*.fna,human*.faa,human*.fna} \
	| gzip -cq >$@

data/ncbi.exonsets.gz data/ncbi.geneinfo.gz data/ncbi.txinfo.gz: data/ncbi.log;
data/ncbi.log: %.log: data/genes.hgnc.gz
	{ gzip -cdq <$< | ncbi-fetch -p $* 2>&1 | tee $@.tmp; } && mv -v $@.tmp $@

data/ucsc.exonsets.gz:
	ucsc-fetch-exonsets && mv ucsc.exonsets.gz data/


############################################################################
## test-data

## These rules build a subset of the database loading files for a set of
## genes.  The genes were selected for diversity of transcript pathologies
## represented.  (see test-data/tx-selection.sql)


#=> test-data -- build test data (currently 4 genes, 4 transcripts)
.PHONY: test-data
test-data: test-data/ncbi.geneinfo.gz test-data/ncbi.txinfo.gz test-data/ncbi.exonsets.gz;


test-data/%.geneinfo.gz: data/%.geneinfo.gz test-data/genes
	gzip -cdq <$< \
	| perl -n -e 'BEGIN{open(F,"$(word 2,$^)"); $$re=join("|",map {chomp;$$_} <F>); print(STDERR "re=$$re\n");}' \
		-e 'print if $$.==1 or m/^(?:$$re)\s/' \
	| gzip -cq >$@
	printf "%d $@\n" $$(gzip -cdq <$@ | wc -l)
test-data/%.exonsets.gz: data/%.exonsets.gz test-data/acs
	gzip -cdq <$< \
	| perl -n -e 'BEGIN{open(F,"$(word 2,$^)"); $$re=join("|",map {chomp;$$_} <F>); print(STDERR "re=$$re\n");}' \
		-e 'print if $$.==1 or m/^(?:$$re)\s/' \
	| gzip -cq >$@
	@printf "%d $@\n" $$(gzip -cdq <$@ | wc -l)
test-data/%.txinfo.gz: data/%.txinfo.gz test-data/acs
	gzip -cdq <$< \
	| perl -aF'\t' -ne 'BEGIN{open(F,"$(word 2,$^)"); $$re=join("|",map {chomp;$$_} <F>); print(STDERR "re=$$re\n");}' \
		-e 'print if $$.==1 or $$F[1] =~ m/^(?:$$re)$$/' \
	| gzip -cq >$@
	@printf "%d $@\n" $$(gzip -cdq <$@ | wc -l)
test-data/%.seqinfo.gz: data/%.seqinfo.gz test-data/acs
	gzip -cdq <$< \
	| perl -aF'\t' -ne 'BEGIN{open(F,"$(word 2,$^)"); $$re=join("|",map {chomp;$$_} <F>); print(STDERR "re=$$re\n");}' \
		-e 'print if $$.==1 or $$F[2] =~ m/^(?:$$re|NC_\d+\.\d+|AC_\d+\.\d+)$$/' \
	| gzip -cq >$@
	@printf "%d $@\n" $$(gzip -cdq <$@ | wc -l)





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
