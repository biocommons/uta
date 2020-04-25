This directory contains custom transcript alignments generated with
splign for loading into UTA.

## Available Transcripts

Andreas requested custom alignments for 18 transcripts. They are shown
below with their status.

### Aligned and can be loaded into UTA:

    NM_000769.4     CYP2C19    aligned
    NM_001025190.1  MSLNL      aligned
    NM_001807.4     CEL        aligned
    NM_002122.3     HLA-DQA1   aligned
    NM_006060.6     IKZF1      aligned
    NM_176886.1     TAS2R45    aligned

### Failed to align and cannot currently be loaded:

    NM_000996.3     RPL35A     terminal unaligned regions
    NM_001261826.2  AP3D1      terminal unaligned regions
    NM_001355436.1  SPTB       terminal unaligned regions
    NM_001428.4     ENO1       terminal unaligned regions
    NM_002116.7     HLA-A      terminal unaligned regions
    NM_006060.5     IKZF1      terminal unaligned regions
    NM_032589.2     DSCR8      terminal unaligned regions
					         
    NM_031421.4     TTC25      internal unaligned region
    NM_001349168.1  DCAF1      internal unaligned region
    NM_001733.5     C1R        internal unaligned region
					         
    NM_001277444.1  NBPF9      low quality; unusable
					         
    NM_002457.4     MUC2       no alignment


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
   - Add to `genomic_region` attribute in txdata.yaml
   
1. Align the transcript using web-based splign
   - Go to https://www.ncbi.nlm.nih.gov/sutils/splign/splign.cgi?textpage=online&level=form
   - Enter the transcript accession in the left box
   - Enter the genomic accession in the right box.
   - Enter the above coordinates in the From and To box. Add/substract
     a large margin (10kb or more).  e.g., 197600000..197690000
   - Optional: Generate list of alignments to perform using
     ./generate-splign-page-params like this: `./generate-splign-page-params txdata.yaml`
	 This step makes it easy to copy paste params and the resulting
     filename to reduce errors.

1. Evaluate the alignment.
   - The alignment should have high coverage (>95%) and identity (>95%). 
   - If the alignment contains an internal gap, it cannot be used.
   - Proceed only if the alignment looks usable.

1. Copy-paste the alignment table
   - Switch to the Text view. (See the `Graphics|Text` button on right.)
   - Copy Text table, including header, into a file like
     `alignments/NM_006060.6-NC_000007.13.splign`
   - If there are multiple alignments, include only the best (first).

1. (Re)Generate loading files
   - `$ ./generate-loading-data alignments/*.splign`. This command
     will write txinfo.gz and exonset.gz.

1. Load these data as described in the UTA loading instructions.


