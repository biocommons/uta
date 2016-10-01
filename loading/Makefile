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
#
# Update flow:
# $ make dev-from-uta_20150903
# $ 

# By default, load test data (i.e., test-{seqinfo,geneinfo,txinfo,exonset})
# into db specified via CONF (which specifies config files in ../etc)



.SUFFIXES:
.PRECIOUS:
.PHONY: FORCE
.DELETE_ON_ERROR:

SHELL:=/bin/bash -o pipefail -e
PATH:=../sbin:${PATH}
SELF:=$(firstword $(MAKEFILE_LIST))
unexport GZIP

CONF=uta_dev@localhost

SRC_NAME:=ncbi/2016-09-08
LOG_DIR:=logs/${CONF}
CONF_FN=../etc/${CONF}.conf
GLOBAL_CONF_FN:=../etc/global.conf
CONF_OPTS:=--conf=${GLOBAL_CONF_FN} --conf=${CONF_FN}
PSQL_ARGS:=-d uta_dev -U uta_admin -h /tmp

############################################################################

SRC_DIR:=data/${SRC_NAME}
LOG_PATHS:=
LOG_PATHS+=$(addsuffix .log,$(subst data/,${LOG_DIR}/,$(wildcard ${SRC_DIR}/*.seqinfo.gz)))
LOG_PATHS+=$(addsuffix .log,$(subst data/,${LOG_DIR}/,$(wildcard ${SRC_DIR}/*.txinfo.gz)))
LOG_PATHS+=$(addsuffix .log,$(subst data/,${LOG_DIR}/,$(wildcard ${SRC_DIR}/*.exonset.gz)))

_:=$(shell mkdir -p ${LOG_DIR})

include .${CONF}.conf.mk
.${CONF}.conf.mk: ${GLOBAL_CONF_FN} ${CONF_FN}
	../dev/conf-to-vars $^ >$@

schema=$(shell python -c 'import uta.models; print uta.models.schema_name')


############################################################################
#= BASIC USAGE
default: help

#=> config -- show variable definitions
config:
	#@echo " = ${}"
	@echo "CONF = ${CONF}"
	@echo "CONF_FN = ${CONF_FN}"
	@echo "CONF_OPTS = ${CONF_OPTS}"
	@echo "GLOBAL_CONF_FN = ${GLOBAL_CONF_FN}"

	@echo "SRC_NAME = ${SRC_NAME}"
	@echo "SRC_DIR = ${SRC_DIR}"
	@echo "LOG_DIR = ${LOG_DIR}"
	@echo "LOG_PATHS = ${LOG_PATHS}"

	@echo "PSQL_ARGS = ${PSQL_ARGS}"

#=> help -- 
help: config
	@../dev/makefile-extract-documentation "${SELF}"



############################################################################
#= Loading rules

load-ncbi-dev:	logs/uta_dev@localhost/${SRC_NAME}/GCF_000001405.25.seqinfo.log	\
		logs/uta_dev@localhost/${SRC_NAME}/GCF_000001405.33.seqinfo.log	\
		logs/uta_dev@localhost/${SRC_NAME}/GCF_000001405.25.txinfo.log  \
		logs/uta_dev@localhost/${SRC_NAME}/GCF_000001405.33.txinfo.log  \
		logs/uta_dev@localhost/${SRC_NAME}/GCF_000001405.25.exonset.log	\
		logs/uta_dev@localhost/${SRC_NAME}/GCF_000001405.33.exonset.log \
		${LOG_DIR}/align-exons.log \
		${LOG_DIR}/merged.assocacs.log
	uta ${CONF_OPTS} analyze
	uta ${CONF_OPTS} refresh-matviews
	uta ${CONF_OPTS} grant-permissions

#=> ${LOG_DIR}/origin.log -- 
load-origin: ${LOG_DIR}/origin.log
${LOG_DIR}/origin.log: data/origin.tsv.gz
	@mkdir -pv ${@D}
	uta ${CONF_OPTS} load-origin $< >$@.tmp 2>&1
	mv $@.tmp $@


#=> ${LOG_DIR}/%seqinfo.log -- 
${LOG_DIR}/%.seqinfo.log: data/%.seqinfo.gz
	@mkdir -pv ${@D}
	uta ${CONF_OPTS} load-seqinfo $< >$@.tmp 2>&1
	mv $@.tmp $@


#=> ${LOG_DIR}/%geneinfo.log -- 
${LOG_DIR}/%.geneinfo.log: data/%.geneinfo.gz
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


#=> ${LOG_DIR}/associated-accessions --
load-assocacs: ${LOG_DIR}/merged.assocacs.log
${LOG_DIR}/merged.assocacs.log: data/merged.assocacs.gz FORCE
	@mkdir -pv ${@D}
	gzip -cd <$< \
	| psql ${PSQL_ARGS} -c "truncate ${schema}.associated_accessions; copy ${schema}.associated_accessions(tx_ac,pro_ac,origin) from STDIN csv header delimiter '	' null '-'" >$@.tmp 2>&1
	mv $@.tmp $@


data/merged.assocacs.gz: data/${SRC_NAME}/assocacs.gz $(wildcard data/aux/assocacs.d/*.gz)
	(zcat $< | head -n1 | cut -f2-4 || true; for f in $^; do zcat $$f | tail -n +2; done | cut -f2-4 | sort -u) | gzip -c >$@.tmp
	mv $@.tmp $@


#=> ${LOG_DIR}/migrate --
migrate-%: ${LOG_DIR}/migrate-%.log;
${LOG_DIR}/migrate-%.log: migrate/%.sql
	@mkdir -pv ${@D}
	psql ${PSQL_ARGS} -e -f $< >$@.tmp 2>&1
	mv $@.tmp $@



#=> analyze -- analyze tables to update statistics
#=> grant-permissions -- so that you can update grants on existing databases
#=> refresh-matviews --
analyze refresh-matviews grant-permissions: %:
	uta ${CONF_OPTS} $*
