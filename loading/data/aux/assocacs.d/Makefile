SHELL:=/bin/bash -e -o pipefail
PATH:=../../../../sbin:${PATH}
.DELETE_ON_ERROR:


default: $(subst .acs,.assocacs.gz,$(wildcard *.acs))

%.assocacs.tsv.gz: %.acs
	(ncbi-fetch-assoc-acs <$< | gzip -c >$@.tmp) 2>$@.log
	mv $@.tmp $@
