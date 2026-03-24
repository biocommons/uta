# Tables

## `associated_accessions`

Many-to-many mapping between transcript (`tx_ac`) and protein (`pro_ac`) accessions.

Useful for mapping between transcript level (e.g. `c.`) and protein-level (`p.`) HGVS expressions. The mapping is many-to-many because updates and alternative annotations are possible on both levels.

| Field Name | Description | Example |
|---|---|---|
| `associated_accession_id` | Surrogate primary key for the association record | `"2882118"` |
| `tx_ac` | Transcript accession | `"NM_000014.4"` |
| `pro_ac` | Protein accession | `"NP_000005.2"` |
| `origin` | Source of assocation | `"NCBI"` |
| `added` | | `"2021-02-03 14:45:47.805895-05"` |

## `exon`

Descriptions of individual exons.

| Field Name | Description | Example |
|---|---|---|
| `exon_id` | *Primary key*. Autoincremented.  | `705444` |
| `exon_set_id` | Foreign key to exon set (i.e. the group of exons on a transcript) | `77142` |
| `start_i` | Starting position (interbase) of the exon upon the aligned transcript sequence | `0` |
| `end_i` | Ending position (interbase) of the exon upon the aligned transcript sequence | `120` |
| `ord` | Ordinal position (0-based) in the exon set (typically, the exon number on the transcript) | `0` |
| `name` | (This field is not currently used.) |  |

## `exon_aln`

Alignment from transcript exons to genomic exons.

| Field Name | Description | Example |
|---|---|---|
| `exon_aln_id` | *Primary key*. Autoincremented. | `268` |
| `tx_exon_id` | Transcript exon. | `772400` |
| `alt_exon_id` | Genomic exon. | `1803115` |
| `cigar` | Description of alignment (in [CIGAR](https://jef.works/blog/2017/03/28/CIGAR-strings-for-dummies/) format) | `"141="` |
| `added` | | `"2014-02-11 05:37:27.983526"` |
| `tx_aseq` | (Not currently used). |  |
| `alt_aseq` | (Not currently used). |  |

## `exon_set`

The set of exons that define an alignment/alignment method between a transcript and a reference genomic sequence.

| Field Name | Description | Example |
|---|---|---|
| `exon_set_id` | *Primary key*. Autoincremented. | `77142` |
| `tx_ac` |  | `"NM_053283.2"` |
| `alt_ac` |  | `"NM_053283.2"` |
| `alt_strand` |  | `1` |
| `alt_aln_method` |  | `"transcript"` |
| `added` |  | `"2014-02-11 00:00:18.455632"` |

## `gene`

Central gene record table. Each row represents an item from an ingested source, i.e. there may be multiple records for many genes.

| Field Name | Description | Example |
|---|---|---|
| `hgnc` | Gene symbol provided by HGNC | `"BRAF"` |
| `maploc` | Cytogenic location | `"7q34"` |
| `descr` |  | `"B-Raf proto-oncogene, serine/threonine kinase"` |
| `summary` |  | `"B-Raf proto-oncogene, serine/threonine kinase"` |
| `aliases` |  | `"B-RAF1,B-raf,BRAF1,NS7,RAFB1"` |
| `added` |  | `"2014-02-10 22:59:21.153414"` |
| `gene_id` | *Primary key*. Bare values are from NCBI; values prefixed with "ENSG" are from Ensembl Gene | `"ENSG00000157764"` |
| `type` | Gene type/functional category. Not provided by all sources. |  |
| `xrefs` |  |  |
| `symbol` | Gene symbol provided by source | `"BRAF"` |

## `origin`

Descriptions of data sources.

| Field Name | Description | Example |
|---|---|---|
| `origin_id` | *Primary key*. Autoincremented. | `3` |
| `name` | Source name | `"NCBI RefSeq"` |
| `descr` | Long source name | `"NCBI RefSeq (nuccore) repository"` |
| `updated` | | `"2014-02-10 21:03:51.332723"` |
| `url` | | `"http://www.ncbi.nlm.nih.gov/refseq/"` |
| `url_ac_fmt` | | `"http://www.ncbi.nlm.nih.gov/nuccore/{ac}"` |

## `seq`

Literal sequences.

| Field Name | Description | Example |
|---|---|---|
| `seq_id` | Hash (sha512t24u?) ID for the sequence | `"fa6e9a58b3bd6dbc6a0a5ad11d99cdc7"` |
| `len` | Sequence length | `39` |
| `seq` | Literal sequence | `"ATGGAATCGACGGTTGATGATGAAGCGCCGGCCGTGTAA"` |

## `seq_anno`

| Field Name | Description | Example |
|---|---|---|
| `seq_anno_id` | *Primary key*. Autoincremented.  | `363473` |
| `seq_id` |  | `"ab954030c30235f49c5b84bd2b914510"` |
| `origin_id` |  | `10` |
| `ac` |  | `ENST00000474039` |
| `descr` |  |  |
| `added` |  | `2015-08-25 23:27:54.765157` |

## `transcript`

| Field Name | Description | Example |
|---|---|---|
| `ac` | Transcript accession | `"NM_004333.5"` |
| `origin_id` | Reference to source of transcript | `1` |
| `cds_start_i` |  | `225` |
| `cds_end_i` |  | `2526` |
| `cds_md5` |  | `"2caedbe1005936f3dab17bb147324963"` |
| `added` |  | `"2017-10-30 20:47:51.277423"` |
| `codon_table` |  | `1` |
| `gene_id` | Source-provided gene ID, sans prefix | `673` |
| `hgnc` | Corresponding HGNC gene symbol | `"BRAF"` |

## `translation_exception`

| Field Name | Description | Example |
|---|---|---|
| `translation_exception_id` | *Primary key*. Autoincremented. | `7` |
| `tx_ac` | Transcript accession. | `"NM_000581.3"` |
| `start_position` |  | `466` |
| `end_position` |  | `469` |
| `amino_acid` |  | `"Sec"` |

# Views

## `tx_exon_aln_mv`

Exon-to-reference sequence alignments.

| Field Name | Description | Example |
|---|---|---|


# Tables (meta)

## `alembic_version`

Metadata for Alembic (migration manager used to generate the database)

## `meta`

Misc key/value store for metadata about the database's creation (eg timestamp, license, library and schema versioning)
