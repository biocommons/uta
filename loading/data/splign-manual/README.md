This directory contains custom transcript alignments generated with
splign for loading into UTA.

To load data into UTA, one needs at least:
* txinfo.gz -- a compressed 
* exonset.gz


## Procedure

For a given RefSeq transcript (e.g., NM_000996.3), do the following:

1. Get the gene and cds info from the refseq record
   - Go to e.g., https://www.ncbi.nlm.nih.gov/nuccore/NM_000996.3
   - From the `gene` section, note the gene symbol
   - From the `CDS` section, note the CDS start and stop (e.g., `65..397`)
   - Click on the gene id to go to the gene page (e.g., `6165`)
   - N.B. Strand is inferred from the orientation of aligned exons.

1. Enter the gene and CDS info in txdata.yaml

1. Get the chromosome and coordinates from the gene page
   - From the "Genomic Context" section, note the chromosomal
     accession and coordinates (e.g., NC_000003.11
     (197677023..197682722))

1. Align the transcript using web-based splign
   - Go to https://www.ncbi.nlm.nih.gov/sutils/splign/splign.cgi?textpage=online&level=form
   - Enter the transcript accession in the left box
   - Enter the genomic accession in the right box.
   - Enter the above coordinates in the From and To box. Add/substract
     a large margin (10kb or more).  e.g., 197600000..197690000

1. Copy-paste the alignment table
   - Put it in a file like `alignments/NM_006060.6-NC_000007.13.splign`

1. (Re)Generate loading files
   - `$ ./generate-loading-data alignments/*.splign`. This command
     will write txinfo.gz and exonset.gz.

1. Load these data as described in the UTA loading instructions.
