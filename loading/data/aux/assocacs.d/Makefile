SHELL:=/bin/bash -e -o pipefail
PATH:=../../../sbin:${PATH}
.DELETE_ON_ERROR:

default: $(subst .acs,.assocacs.gz,$(wildcard *.acs))

%.assocacs.tsv.gz: %.acs
	(ncbi-fetch-assoc-acs <$< | gzip -c >$@.tmp) 2>$@.log
	mv $@.tmp $@

all.filtered.tsv.gz: all.tsv.gz
	(gzip -cdq $< | head -1 || true; gzip -cdq $< | sort -k1,1 -k2,2 -k3,3r | perl -ane 'print unless $$seen{$$F[0].$$F[1]}++') | gzip -c >$@
