.PHONY:
.SUFFIXES:
.DELETE_ON_ERROR:

SHELL:=/bin/bash

uta0-ac-cigars.tsv:
	psql -A -F$$'\t' -d uta -c "select ac,cigars from uta0.transcript_cigars_v order by ac" >$@

uta1-ac-cigars.tsv:
	psql -A -F$$'\t' -d uta_dev -c "select tx_ac as ac,cigars from tx_aln_cigar_dv where alt_ac ~ '^NC_0000' and alt_aln_method = 'splign' order by tx_ac" >$@

u01-cmp.tsv: uta0-ac-cigars.tsv uta1-ac-cigars.tsv
	./cigar-smokeoff $^ >$@
