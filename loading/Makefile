# uta loading Makefile
#
# This Makefile does four things (which is probably too much):
#
# 1. Extracts and translates data from sources into intermediate files
# 2. Creates self-consistent subsets of those data for testing purposes
# 3. Loads intermediate files
# 4. Automates some DB admin tasks (mostly for consistency)
#
#       {sources} --E+T--> {intermediates} ---L---> {db}
#                           ▾          ▴
#                           +--subset--+
#
# Intermediates (and subsets) are stored in data/<setname>/<file>.gz,
# where <file> is one of the TSV formats (see uta/formats/) such as
# exonset, seqinfo, txinfo, or geneinfo. Intermediates are always
# gzip-compressed and this is required for loading.
#
# Loading any intermediate file generates a log file in
# logs/<conf>/<setname>/<file>.log -- that is, it closely parallels
# the structure of intermediate file paths.
# 
# CONFIGURATION
# The environment/Makefile variable CONF is used to specify which conf
# file (in ../etc/) to use. By default, CONF=test. 
# 
# Typical flow:
# $ make cleanest drop create grant-permissions
# $ make load-<dataset> # repeat for all desired sets
# $ make refresh-matviews


.SUFFIXES :
.PRECIOUS :
.PHONY : FORCE
.DELETE_ON_ERROR:

SHELL:=/bin/bash -o pipefail -e
PATH:=../sbin:${PATH}
SELF:=$(firstword $(MAKEFILE_LIST))

# By default, load test data (i.e., test-{seqinfo,geneinfo,txinfo,exonset})
# into db specified via CONF (which specifies config files in ../etc)
DATA=test
CONF=test

DATA_DIR:=${DATA}
LOG_DIR:=logs/${CONF}
CONF_FN=../etc/${CONF}.conf
GLOBAL_CONF_FN:=../etc/global.conf
CONF_OPTS:=--conf=${GLOBAL_CONF_FN} --conf=${CONF_FN}

_:=$(shell mkdir -p ${LOG_DIR})

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
## Source-Specific Extraction and Translation
## TODO: Define how to get sources data

## --- NCBI ---

#=> data/ncbi.exonset.gz data/ncbi.txinfo.gz -- 
data/ncbi.exonset.gz data/ncbi.txinfo.gz: data/ncbi.log;

#=> data/ncbi.log -- 
data/ncbi.log: %.log: mirrors-ncbi/latest/refseq/H_sapiens/alignments/GCF_000001405.25_knownrefseq_alignments.gff3
	(time -p ncbi-gff-import -o NCBI -p $* $< >$@.tmp) 2>&1
	mv -bfv $@.tmp $@

#=> data/ncbi.seqinfo.gz -- 
data/ncbi.seqinfo.gz: data/ncbi.exonset.gz
	(time -p exonset-to-seqinfo -o NCBI $< | gzip -c >$@.tmp) 2>$@.log
	mv -bfv $@.tmp $@

#=> data/ncbi.geneacs.gz -- 
data/ncbi.geneacs.gz:
	(time -p ncbi-fetch-gene-acs | gzip -c >$@.tmp) 2>$@.log
	mv -bfv $@.tmp $@


## --- UCSC ---

#=> data/ucsc.log -- 
data/ucsc.log:
	time -p ucsc-fetch -d ${@D} >$@.tmp 2>&1
	mv -bfv $@.tmp $@

#=> data/ucsc.exonset.gz -- 
data/ucsc.exonset.gz: main/ucsc.log


## ## --- Ensembl ---
## 
## #=> data/ensembl.seqinfo.gz -- 
## data/ensembl.seqinfo.gz: main/ensembl.fasta.gz
## 	fasta-to-seqinfo -o Ensembl $< | gzip -cq >$@.tmp && mv -bfv $@.tmp $@



############################################################################
## Data Subsets

## These rules build a subset of the database loading files for a set of
## genes.  The genes were selected for diversity of transcript pathologies
## represented.  (see test/tx-selection.sql)

SET:=SetA

data/%-${SET}.acs: data/%.txinfo.gz data/${SET}.hgnc
	gzip -cdq <$< | ../sbin/txinfo-filter -G $(word 2,$^) - | sort -u >$@.tmp
	mv -bfv $@.tmp $@

data/%-${SET}.seqinfo.gz: data/%.seqinfo.gz data/${SET}-%.acs
	gzip -cdq <$< | seqinfo-filter -T $(word 2,$^) -R '^[NA]C_' - | gzip -cq >$@
	@printf "%d $@\n" $$(gzip -cdq <$@ | wc -l)

test/%-${SET}.geneinfo.gz: main/%.geneinfo.gz test/genes
	gzip -cdq <$< | geneinfo-filter -G $(word 2,$^) - | gzip -cq >$@
	@printf "%d $@\n" $$(gzip -cdq <$@ | wc -l)

test/%-${SET}.exonset.gz: main/%.exonset.gz test/acs
	gzip -cdq <$< | exonset-filter -T $(word 2,$^) - | gzip -cq >$@
	@printf "%d $@\n" $$(gzip -cdq <$@ | wc -l)

test/%-${SET}.txinfo.gz: main/%.txinfo.gz test/acs
	gzip -cdq <$< | txinfo-filter -T $(word 2,$^) - | gzip -cq >$@
	@printf "%d $@\n" $$(gzip -cdq <$@ | wc -l)



############################################################################
#= Loading

#=> load-% -- 
load-%:
	@lfs=$$(for f in seqinfo geneinfo txinfo exonset; do [ -f data/$*/$$f.gz ] && echo logs/${CONF}/$*/$$f.log; done); \
	[ -n "$$lfs" ] && (set -x; make $$lfs)

#=> load-%-seqinfo -- 
${LOG_DIR}/%/seqinfo.log: data/%/seqinfo.gz
	@mkdir -pv ${@D}
	(time -p uta ${CONF_OPTS} load-seqinfo $<) >$@.tmp 2>&1
	mv $@.tmp $@

#=> load-geneinfo.log -- 
${LOG_DIR}/%/geneinfo.log: data/%/geneinfo.gz
	(time -p uta ${CONF_OPTS} load-geneinfo $<) >$@.tmp 2>&1
	mv $@.tmp $@

#=> load-txinfo.log -- 
${LOG_DIR}/%/txinfo.log: data/%/txinfo.gz
	(time -p uta ${CONF_OPTS} load-txinfo $<) >$@.tmp 2>&1
	mv $@.tmp $@

#=> load-exonset.log -- 
${LOG_DIR}/%/exonset.log: data/%/exonset.gz
	(time -p uta ${CONF_OPTS} load-exonset $<) >$@.tmp 2>&1
	mv $@.tmp $@

#=> align-exons -- 
align-exons: ${LOG_DIR}/align-exons.log
${LOG_DIR}/align-exons.log: FORCE
	(time -p uta ${CONF_OPTS} align-exons) >$@.tmp 2>&1
	mv $@.tmp $@


############################################################################
#= DB Admin

#=> build -- all build steps
# TODO: Rethink whether build should do this much!
build: create grant load-${DATA} align-exons

#=> drop -- 
drop:
	uta ${CONF_OPTS} drop-schema

#=> create -- 
create:
	uta ${CONF_OPTS} create-schema
	uta ${CONF_OPTS} load-sql ../sql/functions.sql ../sql/utils.sql ../sql/views.sql
	uta ${CONF_OPTS} grant-permissions
	uta ${CONF_OPTS} initialize-schema

#=> grant-permissions -- so that you can update grants on existing databases
#=> refresh-matviews -- update materialized views
refresh-matviews grant-permissions: %:
	uta ${CONF_OPTS} $*

# .PHONY: push
# push: push.log
# push.log:
# 	(time pg_dump -U uta_admin -d uta_dev -c -n uta1 | psql -h uta.invitae.com -U uta_admin -d uta_stage -e) >$@.tmp 2>&1
# 	mv $@.tmp $@


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
	/bin/rm -f *~ *.bak *.tmp
#=> cleaner: above, and remove generated files
cleaner: clean
	/bin/rm -f .*.mk
#=> cleanest: above, and remove the virtualenv, .orig, and .bak files
cleanest: cleaner
	/bin/rm -fr logs



#### ############################################################################
#### ## build main data
#### 
#### #=> main/ncbi-core.seqinfo.gz -- 
#### main/ncbi-core.seqinfo.gz:
#### 	fasta-to-seqinfo -o 'NCBI RefSeq' ${SEQ_DIR}/{hs_*.fa,refseq*.fna,human*.faa,human*.fna} \
#### 	| gzip -cq >$@.tmp
#### 	mv -bfv $@.tmp $@
#### 
#### #=> main/ncbi.log -- 
#### main/ncbi.log: %.log: main/genes.hgnc.gz
#### 	{ gzip -cdq <$< | ncbi-fetch -p $* 2>&1 | tee $@.tmp; } && mv -bfv $@.tmp $@
#### 
#### 
#### #=> main/uta0.exonset.gz main/uta0.txinfo.gz main/uta0.fasta.gz -- 
#### main/uta0.exonset.gz main/uta0.txinfo.gz main/uta0.fasta.gz: main/uta0.log;
#### 
#### #=> main/uta0.log -- 
#### main/uta0.log:
#### 	uta0-fetch -d ${@D} >$@.tmp 2>&1 && mv -bfv $@.tmp $@
#### 
#### #=> main/uta0.seqinfo.gz -- 
#### main/uta0.seqinfo.gz: main/uta0.fasta.gz
#### 	fasta-to-seqinfo -o uta0  $< | gzip -cq >$@.tmp && mv -bfv $@.tmp $@


