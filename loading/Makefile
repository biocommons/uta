.SUFFIXES :
.PRECIOUS :
.PHONY : FORCE
.DELETE_ON_ERROR:

SHELL:=/bin/bash -o pipefail
PATH:=../sbin:${PATH}
SELF:=$(firstword $(MAKEFILE_LIST))

DATA_DIR:=${DATA}
CONF=uta_dev@localhost
CONF_FN=../etc/${CONF}.conf
GLOBAL_CONF_FN:=../etc/global.conf
CONF_OPTS:=--conf=${GLOBAL_CONF_FN} --conf=${CONF_FN}


include .${CONF}.conf.mk
.${CONF}.conf.mk: ${GLOBAL_CONF_FN} ${CONF_FN}
	../sbin/conf-to-vars $^ >$@


############################################################################
#= BASIC USAGE
default: help

#=> help -- display this help message
help:
	@extract-makefile-documentation "${SELF}"


############################################################################
#=> db-build -- 
db-create:
	uta ${CONF_OPTS} create-schema
	uta ${CONF_OPTS} create-views ../sql/views.sql
	uta ${CONF_OPTS} initialize-schema

db-grant:
	uta ${CONF_OPTS} grant-permissions

db-load:
	for f in ${DATA_DIR}/*.seqinfo.gz ; do uta ${CONF_OPTS} load-seqinfo  "$$f"; done
	for f in ${DATA_DIR}/*.geneinfo.gz; do uta ${CONF_OPTS} load-geneinfo "$$f"; done
	for f in ${DATA_DIR}/*.txinfo.gz  ; do uta ${CONF_OPTS} load-txinfo   "$$f"; done
	for f in ${DATA_DIR}/*.exonset.gz ; do uta ${CONF_OPTS} load-exonsets "$$f"; done

db-align:
	uta ${CONF_OPTS} align-exons


.PHONY: push
push: push.log
push.log:
	(time pg_dump -U uta_admin -d uta_dev -c -n uta1 | psql -h uta.invitae.com -U uta_admin -d uta_stage -e) >$@.tmp 2>&1
	mv $@.tmp $@


############################################################################
## build main data

main-data: main-ensembl main-ncbi main-ucsc main-uta0

main-ensembl: main/ensembl.seqinfo.gz 
main-ncbi: main/ncbi.seqinfo.gz main/ncbi.exonset.gz main/ncbi.geneinfo.gz main/ncbi.txinfo.gz main/ncbi.fasta.gz main/ncbi-core.seqinfo.gz
main-ucsc: main/ucsc.exonset.gz
main-uta0: main/uta0.exonset.gz main/uta0.txinfo.gz

main/ensembl.seqinfo.gz: main/ensembl.fasta.gz
	fasta-to-seqinfo -o Ensembl $< | gzip -cq >$@.tmp && mv -bfv $@.tmp $@

main/ncbi-core.seqinfo.gz:
	fasta-to-seqinfo -o 'NCBI RefSeq' ${SEQ_DIR}/{hs_*.fa,refseq*.fna,human*.faa,human*.fna} \
	| gzip -cq >$@.tmp
	mv -bfv $@.tmp $@

main/ncbi.exonset.gz main/ncbi.fasta.gz main/ncbi.geneinfo.gz main/ncbi.txinfo.gz: main/ncbi.log;
main/ncbi.log: %.log: main/genes.hgnc.gz
	{ gzip -cdq <$< | ncbi-fetch -p $* 2>&1 | tee $@.tmp; } && mv -bfv $@.tmp $@

main/ucsc.exonset.gz: main/ucsc.log
main/ucsc.log:
	ucsc-fetch -d ${@D} >$@.tmp 2>&1 && mv -bfv $@.tmp $@

main/uta0.exonset.gz main/uta0.txinfo.gz main/uta0.fasta.gz: main/uta0.log;
main/uta0.log:
	uta0-fetch -d ${@D} >$@.tmp 2>&1 && mv -bfv $@.tmp $@
main/uta0.seqinfo.gz: main/uta0.fasta.gz
	fasta-to-seqinfo -o uta0  $< | gzip -cq >$@.tmp && mv -bfv $@.tmp $@


############################################################################
## test-data

## These rules build a subset of the database loading files for a set of
## genes.  The genes were selected for diversity of transcript pathologies
## represented.  (see test/tx-selection.sql)


#=> test-data -- build test data (currently 4 genes, 4 transcripts)
.PHONY: test-data
test-data: \
	test/ncbi.geneinfo.gz test/ncbi.txinfo.gz test/ncbi.exonset.gz test/ncbi.seqinfo.gz test/ncbi-core.seqinfo.gz  \
	test/ensembl.txinfo.gz test/ensembl.exonset.gz test/ensembl.seqinfo.gz \
	test/ucsc.exonset.gz \
	test/uta0.exonset.gz test/uta0.txinfo.gz;


# generate a list of accessions from a list of genes
TEST_TXINFO_FILES:=main/ncbi.txinfo.gz main/ensembl.txinfo.gz
test/acs: test/genes ${TEST_TXINFO_FILES}
	for f in ${TEST_TXINFO_FILES}; do \
	gzip -cdq "$$f" | ../sbin/txinfo-filter -G $< - | tail -n+2 | cut -f 2; \
	done | sort -u >$@

test/%.geneinfo.gz: main/%.geneinfo.gz test/genes
	gzip -cdq <$< | geneinfo-filter -G $(word 2,$^) - | gzip -cq >$@
	@printf "%d $@\n" $$(gzip -cdq <$@ | wc -l)
test/%.exonset.gz: main/%.exonset.gz test/acs
	gzip -cdq <$< | exonset-filter -T $(word 2,$^) - | gzip -cq >$@
	@printf "%d $@\n" $$(gzip -cdq <$@ | wc -l)
test/%.txinfo.gz: main/%.txinfo.gz test/acs
	gzip -cdq <$< | txinfo-filter -T $(word 2,$^) - | gzip -cq >$@
	@printf "%d $@\n" $$(gzip -cdq <$@ | wc -l)
test/%.seqinfo.gz: main/%.seqinfo.gz test/acs
	gzip -cdq <$< | seqinfo-filter -T $(word 2,$^) -R '^[NA]C_' - | gzip -cq >$@
	@printf "%d $@\n" $$(gzip -cdq <$@ | wc -l)





############################################################################
## SETUP

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
