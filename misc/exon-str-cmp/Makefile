.SUFFIXES :
.PRECIOUS :
.PHONY : FORCE

SHELL:=/bin/bash -o pipefail
PATH:=$HOME/projects/uta/bin:${PATH}

SOURCES:=ensembl ucsc uta
PAIRS:=ensembl-ucsc ensembl-uta ucsc-uta

default: $(foreach p,${PAIRS},$p.ex-no-ne $p.ex-no-eq $p.ex-no-diff-histo $p.ex-no-eq-mm)

%.se:
	./bin/fetch-tx-$* | sort -k1,1 >$@

ensembl-ucsc: ensembl.se ucsc.se
	join -t'	' $^ >$@
ensembl-uta: ensembl.se uta.se
	join -t'	' $^ >$@
ucsc-uta: uta.se ucsc.se
	join -t'	' $^ >$@

%.ex-no-ne: %
	perl -lane 'print if $$F[1] != $$F[3]' <$< | sort -k2n,2 >$@
%.ex-no-eq: %
	perl -lane 'print if $$F[1] == $$F[3]' <$< | sort -k2n,2 >$@
%.ex-no-diff-histo: %
	perl -lane 'my $$d = abs($$F[1] - $$F[3]); $$h{$$d}++;' -e 'END { printf("$$_ $$h{$$_}\n") for sort( {$$a<=>$$b} keys(%h)) }' <$< >$@
%.ex-no-eq-mm: %.ex-no-eq
	perl -lane 'print if $$F[2] ne $$F[4]' <$< >$@

%.stats: %.ex-no-eq-mm
	#perl -MList::Util -lane 'my @a = $$F[2] =~ m/\((\d+),\d+\)/g; my @b = $$F[4] =~ m/\((\d+),\d+\)/g; my @d = map {abs($$a[$$_]-$$b[$$_])} 0..$$#a; my $$s = List::Util::reduce {$$a+$$b} @d; print if $$s>10'  $<
	#perl -MList::Util -lane 'my @a = $$F[2] =~ m/\((\d+),\d+\)/g; my @b = $$F[4] =~ m/\((\d+),\d+\)/g; my @d = map {abs($$a[$$_]-$$b[$$_])} 0..$$#a; my $$s = List::Util::reduce {$$a+$$b} @d; print if $$s>100'  $<
	perl -MList::Util -lane 'my @a = $$F[2] =~ m/\((\d+),\d+\)/g; my @b = $$F[4] =~ m/\((\d+),\d+\)/g; my @d = map {abs($$a[$$_]-$$b[$$_])} 0..$$#a; my $$s = List::Util::reduce {$$a+$$b} @d; print if $$s>1000'  $<
