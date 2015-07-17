CREATE OR REPLACE VIEW _cds_exons_v AS
WITH cds_exons as (
SELECT ES.exon_set_id, T.ac AS tx_ac, E.ord,
       E.start_i, E.end_i, 
       CASE WHEN E.end_i >= T.cds_start_i AND E.start_i <= T.cds_end_i THEN greatest(E.start_i,T.cds_start_i) ELSE NULL end AS cds_ex_start_i,
       CASE WHEN E.end_i >= T.cds_start_i AND E.start_i <= T.cds_end_i THEN least(E.end_i,T.cds_end_i) ELSE NULL end AS cds_ex_end_i
FROM transcript T
JOIN exon_set ES ON T.ac = ES.tx_ac AND ES.alt_aln_METHOD = 'transcript'
JOIN exon E ON ES.exon_set_id=E.exon_set_id
WHERE T.cds_start_i IS NOT NULL AND T.cds_end_i IS NOT NULL
)
select *, end_i - start_i as ex_len, cds_ex_end_i - cds_ex_start_i as cds_ex_len from cds_exons
;

CREATE OR replace VIEW _cds_exons_flat_v AS
SELECT exon_set_id,tx_ac,MIN(ord) AS cds_start_exon,MAX(ord) AS cds_end_exon,
       ARRAY_TO_STRING(ARRAY_AGG(format('%s,%s',cds_ex_start_i,cds_ex_end_i) ORDER BY ord),';') AS cds_se_i,
       ARRAY_TO_STRING(ARRAY_AGG(cds_ex_len ORDER BY ord),';') AS cds_exon_lengths
FROM _cds_exons_v
WHERE cds_ex_start_i IS NOT NULL
GROUP BY exon_set_id, tx_ac;


-- See uta-189: 587 ensembl transcripts changed underlying sequence
-- between e-70 and e-79. We will arbitrarily use the most recent to
-- prevent cardinality issues elsewhere.  This is why we should use
-- sequence hashes only.
CREATE OR REPLACE VIEW _seq_anno_most_recent AS
SELECT DISTINCT ON (ac) *
FROM seq_anno
ORDER BY ac,added DESC;


-- TODO: "distinct" below because the same accession might occur in
-- multiple origins.  Transcript definitions use accession only (not
-- origin), which should be fixed in the future. For example, if NCBI
-- and UCSC disagree about exon structure, or the exon structure
-- changes between releases, the use of accession only becomes
-- ambiguous.
CREATE OR REPLACE VIEW _cds_exons_fp_v AS
SELECT SA.seq_id, md5(format('%s;%s',LOWER(SA.seq_id),CTEF.cds_se_i)) AS cds_es_fp,
       md5(cds_exon_lengths) AS cds_exon_lengths_fp, CTEF.*
  FROM _cds_exons_flat_v CTEF
  JOIN _seq_anno_most_recent SA ON CTEF.tx_ac=SA.ac;


