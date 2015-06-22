# uta loading Makefile
#
# This Makefile does four things (which is probably too much):
#
# 1. Extracts and translates data from sources into intermediate files
# 2. Creates self-consistent subsets of those data for testing purposes
# 3. Loads intermediate files from steps 1 or 2
# 4. Automates dba tasks like create and drop (mostly for configuration
#    consistency)
#
#       {sources} --E+T--> {intermediates} ---L---> {db}
#                   (1)     ▾          ▴     (3)
#                           +--subset--+
#                               (2)
#
# Sources are populated in multiple ways. For NCBI, see the
# ncbi-mirrors (a sibling project), which maintains an rsync mirror of
# essential data. UCSC data are fetched directly via mysql.  And
# Ensembl data are pulled via a perl script.
# 
# Intermediates (and subsets) are stored in data/<setname>/<file>.gz,
# where <file> is one of the TSV formats (see uta/formats/) such as
# exonset, seqinfo, txinfo, or geneinfo. Intermediates are always
# gzip-compressed and this is required for loading.  Each set to be a
# self-consistent/complete set of data for loading. (For example, if
# the set is restricted by genes, all transcripts required for that
# gene are present.)
#
# Loading any intermediate file generates a log file in
# logs/<conf>/<setname>/<file>.log -- that is, it closely parallels
# the structure of intermediate file paths with the exception of the
# conf path component so that it's possible to load multiple instances
# without (much) confusion.
# 
# CONFIGURATION
# The environment/Makefile variable CONF is used to specify which conf
# file (in ../etc/) to use. By default, CONF=test. 
# 
# Typical flow:
# $ make cleanest drop create
# $ make load-<dataset> # repeat for all desired sets
# $ make refresh-matviews


.SUFFIXES:
.PRECIOUS:
.PHONY: FORCE
.DELETE_ON_ERROR:

SHELL:=/bin/bash -o pipefail -e
PATH:=../sbin:${PATH}
SELF:=$(firstword $(MAKEFILE_LIST))
unexport GZIP

# By default, load test data (i.e., test-{seqinfo,geneinfo,txinfo,exonset})
# into db specified via CONF (which specifies config files in ../etc)
DATA=test
CONF=uta_dev@localhost

DATA_DIR:=${DATA}
LOG_DIR:=logs/${CONF}
CONF_FN=../etc/${CONF}.conf
GLOBAL_CONF_FN:=../etc/global.conf
CONF_OPTS:=--conf=${GLOBAL_CONF_FN} --conf=${CONF_FN}

_:=$(shell mkdir -p ${LOG_DIR})

include .${CONF}.conf.mk
.${CONF}.conf.mk: ${GLOBAL_CONF_FN} ${CONF_FN}
	../sbin/conf-to-vars $^ >$@

schema=$(shell python -c 'import uta.models; print uta.models.schema_name')

############################################################################
#= BASIC USAGE
default: help

#=> help -- 
help:
	@extract-makefile-documentation "${SELF}"


############################################################################
## Source-Specific Extraction and Translation

## --- NCBI ---
## Using NCBI data structures is a bit like playing Thimblerig with
## Romulans at an archaeological dig.  The current flow is:
## gene/DATA/gene_info.gz     --> geneinfo.gz
## gene/DATA/gene2refseq.gz   --> geneacs.gz ---------+
## refseq/mRNA_protein/(gbff) --> gbff.txinfo.gz  --v v
## refseq/assembly/(gff)      ---------------------------> txinfo, exonset
##
## NOTES:
## 1) In this process, the gbff files provide only the cds start and
## end. To my knowledge, gbff and eutils are the only sources of cds
## s,e.
## 2) In principle, geneinfo and geneacs could be built from gbff
## instead, and probably should be for more likely consistency.
## 3) I've learned the hard way that none of the above files are
## guaranteed to be synchronized. For example, on 2015-05-18, 4190
## accessions in refseq/alignments are not in in gbff files, and
## another 583 that are common have different exon structures. (A
## small minority of these are likely transcripts with misc_feature
## features.)

MIRRORS_NCBI_ROOT:=aux/mirrors-ncbi/2015/05/16

#=> data/ncbi/geneinfo.gz -- 
data/ncbi/geneinfo.gz: ${MIRRORS_NCBI_ROOT}/gene/DATA/GENE_INFO/Mammalia/Homo_sapiens.gene_info.gz
	@mkdir -pv ${@D}
	(ncbi-parse-geneinfo $< | gzip -c >$@.tmp) 2>$@.log
	mv -bfv $@.tmp $@

#=> data/ncbi/geneacs.gz -- 
# filtering records in python is slow; prefilter humans (tax_id=9606)
data/ncbi/geneacs.gz: data/ncbi/gene2refseq_9606.gz
	ncbi-parse-gene2refseq $< | gzip -c >$@.tmp 2>$@.log
	mv -bfv $@.tmp $@
.PRECIOUS: /tmp/gene2refseq_9606.gz
data/ncbi/gene2refseq_9606.gz: ${MIRRORS_NCBI_ROOT}/gene/DATA/gene2refseq.gz
	gzip -cdq <$< | perl -ne 'print if m/^#|^9606\t/' | gzip -c >$@.tmp
	mv -bfv $@.tmp $@

#=> data/ncbi/gbff.txinfo.gz -- 
data/ncbi/gbff.txinfo.gz: $(sort $(wildcard ${MIRRORS_NCBI_ROOT}/refseq/H_sapiens/mRNA_Prot/human.?.rna.gbff.gz))
	@mkdir -pv ${@D}
	ncbi-parse-gbff $^ | gzip -c >$@.tmp
	mv -bfv $@.tmp $@

#=> data/ncbi/exonset.gz data/ncbi/txinfo.gz -- 
data/ncbi/exonset.gz data/ncbi/txinfo.gz: ${MIRRORS_NCBI_ROOT}/refseq/H_sapiens/alignments/GCF_000001405.25_knownrefseq_alignments.gff3 data/ncbi/geneacs.gz data/ncbi/gbff.txinfo.gz
	@mkdir -pv ${@D}
	ncbi-parse-gff -G $(word 2,$^) -T $(word 3,$^) -p ${@D}/ $< >${@D}/ncbi-parse-gff.log 2>&1

#=> data/ncbi/seqinfo.gz -- 
data/ncbi/seqinfo.gz: data/ncbi/exonset.gz
	@mkdir -pv ${@D}
	(exonset-to-seqinfo -o NCBI $< | gzip -c >$@.tmp) 2>$@.log
	mv -bfv $@.tmp $@



## --- UCSC ---

## You gotta love how easy ucsc makes it to get data. Thanks guys and gals!

#=> data/ucsc-{hg19,hg38}/exonset.gz -- 
data/ucsc-%/exonset.gz: data/ucsc-%/log;
data/ucsc-%/log:
	@mkdir -pv ${@D}
	ucsc-fetch -D $* -p ${@D}/ >$@.tmp 2>&1
	mv -bfv $@.tmp $@


## --- Ensembl ---

#=> data/ensembl-%seqinfo.gz data/ensembl-%txinfo.gz data/ensembl-%exonset.gz
data/ensembl-%/seqinfo.gz data/ensembl-%/txinfo.gz data/ensembl-%/exonset.gz: data/ensembl-%/log

#=> data/ensembl-%log --
data/ensembl-%/log:
	@if ! mkdir ${@D}; then echo "${@D} exists: move it out of the way in order to update" 1>&2; exit 1; fi
	ENSEMBL_VERSION=$* source ../etc/ensembl.sh; ensembl-fetch --prefix ${@D}/ >$@.tmp 2>&1
	mv -bfv $@.tmp $@


## --- Generic rules ---
##X:%seqinfo.gz 
#=> data/%/seqinfo.gz -- 
data/%/seqinfo.gz: data/%/fasta.gz
	fasta-to-seqinfo -o $*  $< | gzip -cq >$@.tmp
	mv -bfv $@.tmp $@


############################################################################
## Data Subsets

## These rules build a subset of the database loading files for a set
## of genes (in aux/gene-sets/).

## This set of rules involves some esoteric Makefile magic.  First,
## the define section defines a template block of rules. That block is
## instantiated once per gene set discovered in aux/gene-sets/ by the
## $(eval $(call ... )) section that follows.



define subset_block
$(notice subset-%/$(1))

.PHONY: subset-ensembl-79/$(1)
subset-ensembl-79/$(1): $$(foreach f,txinfo seqinfo exonset,data/ensembl-79/$(1)/$$f.gz);

.PHONY: subset-%/$(1)
subset-%/$(1): $$(foreach f,txinfo seqinfo geneinfo exonset,data/%/$(1)/$$f.gz);

.PRECIOUS: data/%/$(1)/txinfo.gz
data/%/$(1)/txinfo.gz: data/%/txinfo.gz aux/gene-sets/$(1).hgnc
	@mkdir -pv $${@D}
	gzip -cdq <$$< | ../sbin/txinfo-filter -G $$(word 2,$$^) - | gzip -c >$$@.tmp
	mv -bfv $$@.tmp $$@

.PRECIOUS: data/%/$(1)/acs
data/%/$(1)/acs: data/%/$(1)/txinfo.gz
	@mkdir -pv $${@D}
	gzip -cdq <$$< | tail -n+2 | cut -f2 | sort -u >$$@.tmp
	mv -bfv $$@.tmp $$@

.PRECIOUS: data/%/$(1)/seqinfo.gz
data/%/$(1)/seqinfo.gz: data/%/seqinfo.gz data/%/$(1)/acs
	@mkdir -pv $${@D}
	gzip -cdq <$$< | seqinfo-filter -T $$(word 2,$$^) -R '^[NA]C_' - | gzip -cq >$$@
	@printf "%d $$@\n" $$$$(gzip -cdq <$$@ | wc -l)

.PRECIOUS: data/%/$(1)/geneinfo.gz
data/%/$(1)/geneinfo.gz: data/%/geneinfo.gz aux/gene-sets/$(1).hgnc
	@mkdir -pv $${@D}
	gzip -cdq <$$< | geneinfo-filter -G $$(word 2,$$^) - | gzip -cq >$$@
	@printf "%d $$@\n" $$$$(gzip -cdq <$$@ | wc -l)

.PRECIOUS: data/%/$(1)/exonset.gz
$(notice data/%/$(1)/exonset.gz: data/%/exonset.gz data/%/$(1)/acs)
data/%/$(1)/exonset.gz: data/%/exonset.gz data/%/$(1)/acs
	gzip -cdq <$$< | exonset-filter -T $$(word 2,$$^) - | gzip -cq >$$@
	@printf "%d $$@\n" $$$$(gzip -cdq <$$@ | wc -l)
endef

data/ucsc-hg19/%/acs data/ucsc-hg38/%/acs: data/ncbi/%/acs
	@mkdir -pv ${@D}
	ln -rs $< $@

GENESETS=$(subst .hgnc,,$(notdir $(wildcard aux/gene-sets/*.hgnc)))
$(foreach gs,${GENESETS},$(eval $(call subset_block,${gs})))


############################################################################
#= Loading sets

# core data that needs to be loaded
load-base: ${LOG_DIR}/ncbi/preferred-accessions.log

load-bic:        $(foreach f,         seqinfo txinfo exonset,${LOG_DIR}/bic/$f.log)
load-ensembl-79: $(foreach f,         seqinfo txinfo exonset,${LOG_DIR}/ensembl-79/$f.log)
load-ncbi:       $(foreach f,geneinfo seqinfo txinfo exonset,${LOG_DIR}/ncbi/$f.log)
load-ucsc-hg19:  $(foreach f,                        exonset,${LOG_DIR}/ucsc-hg19/$f.log)
load-ucsc-hg38:  $(foreach f,                        exonset,${LOG_DIR}/ucsc-hg38/$f.log)

load-ncbi/refmismatch: $(foreach f,geneinfo seqinfo txinfo exonset,${LOG_DIR}/ncbi/refmismatch/$f.log)  
load-ensembl-79/refmismatch: $(foreach f,seqinfo txinfo exonset,${LOG_DIR}/ensembl-79/refmismatch/$f.log)

load-ncbi/acmg-mr: $(foreach f,geneinfo seqinfo txinfo exonset,${LOG_DIR}/ncbi/acmg-mr/$f.log)  
load-ensembl-79/acmg-mr: $(foreach f,seqinfo txinfo exonset,${LOG_DIR}/ensembl-79/acmg-mr/$f.log)

############################################################################
#= Loading rules

#=> ${LOG_DIR}/origin.log -- 
${LOG_DIR}/origin.log: data/origin.tsv
	@mkdir -pv ${@D}
	uta ${CONF_OPTS} load-origin $< >$@.tmp 2>&1
	mv $@.tmp $@

#=> ${LOG_DIR}/%seqinfo.log -- 
${LOG_DIR}/%seqinfo.log: data/%seqinfo.gz
	@mkdir -pv ${@D}
	uta ${CONF_OPTS} load-seqinfo $< >$@.tmp 2>&1
	mv $@.tmp $@

#=> ${LOG_DIR}/%geneinfo.log -- 
${LOG_DIR}/%geneinfo.log: data/%geneinfo.gz
	@mkdir -pv ${@D}
	uta ${CONF_OPTS} load-geneinfo $< >$@.tmp 2>&1
	mv $@.tmp $@

#=> ${LOG_DIR}/%txinfo.log -- 
${LOG_DIR}/%txinfo.log: data/%txinfo.gz
	@mkdir -pv ${@D}
	uta ${CONF_OPTS} load-txinfo $< >$@.tmp 2>&1
	mv $@.tmp $@

#=> ${LOG_DIR}/%exonset.log -- 
${LOG_DIR}/%exonset.log: data/%exonset.gz
	@mkdir -pv ${@D}
	uta ${CONF_OPTS} load-exonset $< >$@.tmp 2>&1
	mv $@.tmp $@

#=> align-exons -- 
#=> ${LOG_DIR}/align-exons.log -- 
align-exons: ${LOG_DIR}/align-exons.log
${LOG_DIR}/align-exons.log: FORCE
	@mkdir -pv ${@D}
	uta ${CONF_OPTS} align-exons >$@.tmp 2>&1
	mv $@.tmp $@

#=> ${LOG_DIR}/preferred-accessions --
${LOG_DIR}/ncbi/preferred-accessions.log: data/ncbi/geneacs.gz
	@mkdir -pv ${@D}
	gzip -cd <$< \
	| psql -d uta_dev -U uta_admin  -c "copy ${schema}.preferred_accession(hgnc,tx_ac,pro_ac,origin) from STDIN csv header delimiter '	' null '-'" >$@.tmp 2>&1
	mv $@.tmp $@



############################################################################
#= DB Admin

#=> drop -- 
drop:
	uta ${CONF_OPTS} drop-schema

#=> create -- 
create:
	uta ${CONF_OPTS} create-schema
	uta ${CONF_OPTS} load-sql ../sql/internal-views.sql ../sql/views.sql ../sql/preferred_accession.sql
	uta ${CONF_OPTS} grant-permissions
	uta ${CONF_OPTS} load-origin data/origin.tsv

post-load: analyze refresh-matviews 

#=> analyze -- analyze tables to update statistics
#=> grant-permissions -- so that you can update grants on existing databases
#=> refresh-matviews --
analyze refresh-matviews grant-permissions: %:
	uta ${CONF_OPTS} $*


# push uta_dev/uta1 to 
push-dev:
	psql -h uta.invitae.com -U uta_admin -d 


mega-test:
	make cleanest drop create
	make load-base
	make load-ncbi/{refmismatch,acmg-mr}
	make load-ensembl-79/{refmismatch,acmg-mr}
	make align-exons refresh-matviews

the-whole-kielbasa:
	make cleanest drop create
	make load-base
	make load-ncbi
	make load-ensembl-79
	make load-bic
	make load-ucsc-hg19
	make align-exons refresh-matviews


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
#### ## SETUP
#### 
#### #=> setup-perl: install perl packages
#### # TODO: consider perl brew instead
#### setup-perl:
#### 	./sbin/perl-module-install --install-base ve   Log::Log4perl


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


