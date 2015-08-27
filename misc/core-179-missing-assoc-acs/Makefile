SHELL:=/bin/bash -o pipefail

core-179.assocacs.gz: core-179.acs
	./fetch <$< | gzip -c >$@.tmp
	mv $@.tmp $@


