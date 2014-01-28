.SUFFIXES :
.PRECIOUS :
.PHONY : FORCE

SHELL:=/bin/bash -o pipefail

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


############################################################################
### CLEANUP
.PHONY: clean cleaner cleanest pristine
clean:
	find . -name \*~ -print0 | xargs -0r /bin/rm
cleaner: clean
	find . \( -name \*.orig -o -name \*.bak \) -print0 | xargs -0r /bin/rm -v
cleanest: cleaner
pristine: cleanest
	# deleting anything unknown to mercurial, including your
	# precious uncommitted changes
	hg st -un0 | xargs -0r echo /bin/rm -fv
