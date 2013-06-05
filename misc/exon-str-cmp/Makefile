.SUFFIXES :
.PRECIOUS :
.PHONY : FORCE

SHELL:=/bin/bash -o pipefail
PATH:=$HOME/projects/uta/bin:$PATH


default: uta-ucsc ex-no-ne ex-no-eq ex-no-diff-histo eq-ex-no-mm

ucsc.se:
	./bin/fetch-tx-ucsc | sort -k1,1 >$@
uta.se:
	./bin/fetch-tx-uta | sort -k1,1 >$@
uta-ucsc: uta.se ucsc.se
	join -t'	' $^ >$@


ex-no-ne: uta-ucsc
	perl -lane 'print if $$F[1] != $$F[3]' <$< | sort -k2n,2 >$@

ex-no-eq: uta-ucsc
	perl -lane 'print if $$F[1] == $$F[3]' <$< | sort -k2n,2 >$@

ex-no-diff-histo: uta-ucsc
	perl -lane 'my $$d = abs($$F[1] - $$F[3]); $$h{$$d}++;' -e 'END { printf("$$_ $$h{$$_}\n") for sort( {$$a<=>$$b} keys(%h)) }' <$< >$@

ex-no-eq-mm: ex-no-eq
	perl -lane 'print if $$F[2] ne $$F[4]' <$< >$@

