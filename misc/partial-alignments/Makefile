.DELETE_ON_ERROR:
.PHONY: FORCE
.PRECIOUS:
.SUFFIXES:

SHELL:=bash -o pipefail

VPATH:=mirrors-ncbi/2019/09/05/refseq/H_sapiens/alignments

ASSYS:=GRCh37.p13 GRCh38.p2 GRCh38.p7 GRCh38.p12


default: $(foreach a,${ASSYS},$a/tx $a/warnings $a/warnings-tx $a/clean-tx)


GRCh37.p13/gff: GCF_000001405.25_knownrefseq_alignments.gff3
	mkdir -p ${@D}
	cd ${@D}; ln -fns ../$< ${@F}
GRCh38.p2/gff: GCF_000001405.28_knownrefseq_alignments.gff3
	mkdir -p ${@D}
	cd ${@D}; ln -fns ../$< ${@F}
GRCh38.p7/gff: GCF_000001405.33_knownrefseq_alignments.gff3
	mkdir -p ${@D}
	cd ${@D}; ln -fns ../$< ${@F}
GRCh38.p12/gff: GCF_000001405.38_knownrefseq_alignments.gff3
	mkdir -p ${@D}
	cd ${@D}; ln -fns ../$< ${@F}


%/tx: %/gff
	perl -lne 'print $$1 if m/Target=(\S+)/' <$< | sort -u >$@

%/warnings: %/gff
	./find-partial-alignments $< >$@ 2>&1

%/warnings-tx: %/warnings
	perl -lne 'print $$1 if m/~([.\w]+)/' <$< | sort -u >$@

%/clean-tx: %/tx %/warnings-tx
	join -v1 $^ >$@
