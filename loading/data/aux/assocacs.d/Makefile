SHELL:=/bin/bash -o pipefail
PATH:=../../../sbin:${PATH}

default: $(subst .acs,.assocacs.gz,$(wildcard *.acs))

%.assocacs.gz: %.acs
	(ncbi-fetch-assoc-acs <$< | gzip -c >$@.tmp) 2>$@.log
	mv $@.tmp $@
