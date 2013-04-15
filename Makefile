.PHONY:
.SUFFIXES:
.DELETE_ON_ERROR:

CONDITIONS_DIR:=/locus/data/conditions/2.2.0/MiseqMay2012

condition-genes:
	perl -ln0e 'print $1 if m/hgnc-name="(.+?)"/' ${CONDITIONS_DIR}/conditionxml/Condition_*.xml \
	| sort -u >$@

refgenes:
	mysql -AN -qB -h genome-mysql.cse.ucsc.edu -u genome -D hg19 \
	-e 'select distinct name2 from refGene' >$@

nm-enst-equiv:
	# expect 2.5h on localhost ensembl, 6.5h on private
	bin/ensembl-nm-enst-equiv $$(seq 1 22) X Y >$@

load-nm-enst-equiv: load-%: %
	grep -v '^#' $< \
	| egrep -v 'ENST00000390321|ENST00000443402|ENST00000526893' \
	| sort -u \
	| psql -c '\copy nm_enst_equiv from STDIN' >$@



setup: install-perl-modules


install-perl-modules:
	./sbin/perl-module-install --install-base ve   Log::Log4perl
