## Using the NCBI ftp site is a bit like playing Thimblerig with
## Romulans at a deep space archaeological outpost.
## 
## The current flow is:
## gene/DATA/gene_info.gz     --> geneinfo.gz
## gene/DATA/gene2refseq.gz   --> assocacs.gz --------+
## refseq/mRNA_protein/(gbff) --> gbff.txinfo.gz  --v v
## refseq/assembly/(gff)      ---------------------------> txinfo, exonset
##
## NOTES:
## 1) In this process, the gbff files provide only the cds start and
## end. To my knowledge, gbff and eutils are the only sources of cds
## s,e.
## 2) In principle, geneinfo and assocacs could be built from gbff
## instead, and probably should be for more likely consistency.
## 3) I've learned the hard way that none of the above files are
## guaranteed to be synchronized. For example, on 2015-05-18, 4190
## accessions in refseq/alignments are not in in gbff files, and
## another 583 that are common have different exon structures. (A
## small minority of these are likely transcripts with misc_feature
## features.)


.SUFFIXES:
.PRECIOUS:
.PHONY: FORCE
.DELETE_ON_ERROR:

SHELL:=/bin/bash -o pipefail -e
PATH:=../../../sbin:${PATH}
SELF:=$(firstword $(MAKEFILE_LIST))
unexport GZIP

_:=$(shell mkdir -p tmp)


src: FORCE
	mkdir -p $@
	rsync --no-motd -HRavP ftp.ncbi.nlm.nih.gov::gene/DATA/GENE_INFO/Mammalia/Homo_sapiens.gene_info.gz src/gene/
	rsync --no-motd -HRavP ftp.ncbi.nlm.nih.gov::gene/DATA/gene2refseq.gz src/gene/
	rsync --no-motd -HRavP ftp.ncbi.nlm.nih.gov::refseq/H_sapiens/mRNA_Prot src/refseq/
	rsync --no-motd -HRavP ftp.ncbi.nlm.nih.gov::refseq/H_sapiens/alignments/*{knownrefseq,refseqgene}*.gff3 src/refseq


all: geneinfo.gz assocacs.gz gbff.txinfo.gz exonset.gz seqinfo.gz


#=> geneinfo.gz -- 
geneinfo.gz: src/gene/DATA/GENE_INFO/Mammalia/Homo_sapiens.gene_info.gz
	(ncbi-parse-geneinfo $< | gzip -c >$@.tmp) 2>$@.log
	mv -bfv $@.tmp $@

#=> assocacs.gz -- 
# filtering records in python is slow; prefilter humans (tax_id=9606)
.PRECIOUS: /tmp/gene2refseq_9606.gz
gene2refseq_9606.gz: src/gene/DATA/gene2refseq.gz
	gzip -cdq <$< | perl -ne 'print if m/^#|^9606\t/' | gzip -c >$@.tmp
	mv -bfv $@.tmp $@
assocacs.gz: gene2refseq_9606.gz
	ncbi-parse-gene2refseq $< | gzip -c >$@.tmp 2>$@.log
	mv -bfv $@.tmp $@

#=> gbff.txinfo.gz -- build transcript definitions from gbff files
# N.B. the main use of these is to build a map of ac->hgnc for the ncbi/txinfo files
# Since we only care about NM and NR, prefilter those files to save parse time
GBFF_DIR:=src/refseq/H_sapiens/mRNA_Prot
GBFF_FILES:=$(wildcard ${GBFF_DIR}/human.*.rna.gbff.gz)
GBFF_BASES:=$(sort $(subst ${GBFF_DIR}/,,${GBFF_FILES}))
.PRECIOUS: tmp/%.gbff.gz
tmp/%.gbff.gz: ${GBFF_DIR}/%.gbff.gz
	gzip -cdq $< | perl -ne 'BEGIN {$$/="//\n"} while (<>) {print if m/^LOCUS\s+N[RM]/}' | gzip -c >$@.tmp
	mv -bfv $@.tmp $@
gbff.txinfo.gz: $(addprefix tmp/,${GBFF_BASES})
	((zgrep -El 'LOCUS\s+N[MR]' $^ || true) | xargs -r ncbi-parse-gbff | gzip -c >$@.tmp) 2>$@.log.tmp
	mv -bfv $@.tmp $@; mv -bfv $@.log.tmp $@.log

#=> exonset.gz txinfo.gz -- build exonset definitions from gff files
exonset.gz txinfo.gz: src/refseq/H_sapiens/alignments/GCF_000001405.25_knownrefseq_alignments.gff3 assocacs.gz gbff.txinfo.gz
	ncbi-parse-gff -G $(word 2,$^) -T $(word 3,$^) -p ${@D}/ $< >${@D}/ncbi-parse-gff.log 2>&1

#=> seqinfo.gz -- 
seqinfo.gz: exonset.gz
	(exonset-to-seqinfo -o NCBI $< | gzip -c >$@.tmp) 2>$@.log
	mv -bfv $@.tmp $@



############################################################################
#= CLEANUP
.PHONY: clean cleaner cleanest pristine
#=> clean: clean up editor backups, etc.
clean:
	/bin/rm -f *~ *.bak *.tmp
#=> cleaner: above, and remove generated files
cleaner: clean
	/bin/rm -f .*.mk
#=> cleanest: above, and remove the virtualenv, .orig, and .bak files
cleanest: cleaner
	/bin/rm -fr logs


.PRECIOUS: %.sha1
%.sha1: %
	(cd "${<D}"; sha1sum "${<F}") >"$@.tmp"
	/bin/mv "$@.tmp" "$@"

