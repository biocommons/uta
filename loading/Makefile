# uta loading Makefile

.SUFFIXES :
.PRECIOUS :
.PHONY : FORCE
.DELETE_ON_ERROR:

SHELL:=/bin/bash -o pipefail -e
PATH:=../sbin:${PATH}
SELF:=$(firstword $(MAKEFILE_LIST))

DATA=test
CONF=test

DATA_DIR:=${DATA}
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
#= Creating and Loading

#=> build -- all build steps
build: create grant load-${DATA} align-exons


#=> drop -- 
drop:
	uta ${CONF_OPTS} drop-schema


#=> uta-create -- 
create:
	uta ${CONF_OPTS} create-schema
	uta ${CONF_OPTS} load-sql ../sql/functions.sql ../sql/utils.sql ../sql/views.sql
	uta ${CONF_OPTS} grant-permissions
	uta ${CONF_OPTS} initialize-schema


#=> uta-grant -- so that you can update grants on existing databases
grant:
	uta ${CONF_OPTS} grant-permissions


#=> load-% -- 
load-%:
	make -k $(foreach t,seqinfo geneinfo txinfo exonset,logs/load-$*.$t.log) align-exons


#=> load-%-seqinfo -- 
load-%-seqinfo: logs/load-%-seqinfo.log;
logs/load-%.seqinfo.log: data/%.seqinfo.gz
	(time -p uta ${CONF_OPTS} load-seqinfo $<) >$@.tmp 2>&1
	mv $@.tmp $@


#=> load-geneinfo.log -- 
load-%-geneinfo: logs/load-%.geneinfo.log;
logs/load-%.geneinfo.log: data/%.geneinfo.gz
	(time -p uta ${CONF_OPTS} load-geneinfo $<) >$@.tmp 2>&1
	mv $@.tmp $@


#=> load-txinfo.log -- 
load-%-txinfo: logs/load-%-txinfo.log;
logs/load-%.txinfo.log: data/%.txinfo.gz
	(time -p uta ${CONF_OPTS} load-txinfo $<) >$@.tmp 2>&1
	mv $@.tmp $@


#=> load-exonset.log -- 
load-%-exonset: logs/load-%-exonset.log;
logs/load-%.exonset.log: data/%.exonset.gz
	(time -p uta ${CONF_OPTS} load-exonset $<) >$@.tmp 2>&1
	mv $@.tmp $@


#=> align-exons -- 
align-exons: logs/align-exons.log
logs/align-exons.log:
	(time -p uta ${CONF_OPTS} align-exons) >$@.tmp 2>&1
	mv $@.tmp $@



# .PHONY: push
# push: push.log
# push.log:
# 	(time pg_dump -U uta_admin -d uta_dev -c -n uta1 | psql -h uta.invitae.com -U uta_admin -d uta_stage -e) >$@.tmp 2>&1
# 	mv $@.tmp $@



############################################################################
## Source-Specific Extraction and Translation

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

data/setA-%.acs: data/%.txinfo.gz data/setA.hgnc
	gzip -cdq <$< | ../sbin/txinfo-filter -G $(word 2,$^) - | sort -u >$@.tmp
	mv -bfv $@.tmp $@

data/setA-%.seqinfo.gz: data/%.seqinfo.gz data/setA-%.acs
	gzip -cdq <$< | seqinfo-filter -T $(word 2,$^) -R '^[NA]C_' - | gzip -cq >$@
	@printf "%d $@\n" $$(gzip -cdq <$@ | wc -l)

test/%.geneinfo.gz: main/%.geneinfo.gz test/genes
	gzip -cdq <$< | geneinfo-filter -G $(word 2,$^) - | gzip -cq >$@
	@printf "%d $@\n" $$(gzip -cdq <$@ | wc -l)

test/%.exonset.gz: main/%.exonset.gz test/acs
	gzip -cdq <$< | exonset-filter -T $(word 2,$^) - | gzip -cq >$@
	@printf "%d $@\n" $$(gzip -cdq <$@ | wc -l)

test/%.txinfo.gz: main/%.txinfo.gz test/acs
	gzip -cdq <$< | txinfo-filter -T $(word 2,$^) - | gzip -cq >$@
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
	/bin/rm -f *~ *.bak *.tmp
#=> cleaner: above, and remove generated files
cleaner: clean
	/bin/rm -f .*.mk
#=> cleanest: above, and remove the virtualenv, .orig, and .bak files
cleanest: cleaner
	/bin/rm -f *.log logs/*



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


