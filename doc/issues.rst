Known Issues

* Mapping in a region of ambiguous alignments is ambiguous.
Consider the following alignment:

  AAATAGCACGATACAA--CCGCACCAGCTACTGGG
  --ATAGCACGATACAACCCCGCACCAGCTACT--G

This alignment demonstrate the effect of the left-right associativity bias
in the aligner for equal scores. Note that the left side of this alignment
could equally be AAAT../A--T.., the middle gap could be
..ACC--G../..ACCCCG.., and the right side could be ..TGGG/..TG--. Because
these each excerpt is equivalent its correspondant in the alignment above,
mapping variants within the left-right extrema of the gap ambiguity is
ambiguous.

We currently don't have an easy way to identify and warn users who attempt
to map in such regions.

Why it matters: In PNPLA4, exon 5, we have this genomic sequence (top),
the current alignment, and an alternative:
GTCCTCCTAGCCAGCAGTTTTGTGCCCATTTATGCAGGACTGAAGCTAGTGGAATACAAAGGGCAGGTAAG
GTCCTCCTAGCCAGCAGTTTTGTGCCCATTTATGCAGGACTGAAGCTAGTGGAATACAAAGGGC-----AG
GTCCTCCTAGCCAGCAGTTTTGTGCCCATTTATGCAGGACTGAAGCTAGTGGAATACAAAGGGCAG-----

The alternative alignment is more likely given the canonical 5' splice
site (GT). 

