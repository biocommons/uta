show search_path;

CREATE OR REPLACE VIEW _cds_exons_v AS
SELECT ES.exon_set_id, T.ac AS tx_ac, E.ord,
       E.start_i, E.end_i,
       CASE WHEN E.end_i >= T.cds_start_i AND E.start_i <= T.cds_end_i THEN greatest(E.start_i,T.cds_start_i) ELSE NULL end AS cds_ex_start_i,
       CASE WHEN E.end_i >= T.cds_start_i AND E.start_i <= T.cds_end_i THEN least(E.end_i,T.cds_end_i) ELSE NULL end AS cds_ex_end_i
FROM transcript T
JOIN exon_set ES ON T.ac = ES.tx_ac AND ES.alt_aln_METHOD = 'transcript'
JOIN exon E ON ES.exon_set_id=E.exon_set_id
WHERE T.cds_start_i IS NOT NULL AND T.cds_end_i IS NOT NULL;

CREATE OR replace VIEW _cds_exons_flat_v AS
SELECT exon_set_id,tx_ac,MIN(ord) AS cds_start_exon,MAX(ord) AS cds_end_exon,
       ARRAY_TO_STRING(ARRAY_AGG(format('%s,%s',cds_ex_start_i,cds_ex_end_i) ORDER BY ord),';') AS cds_se_i
FROM _cds_exons_v
WHERE cds_ex_start_i IS NOT NULL
GROUP BY exon_set_id, tx_ac;

-- TODO: "distinct" below because the same accession might occur in
-- multiple origins.  Transcript definitions use accession only (not
-- origin), which should be fixed in the future. For example, if NCBI
-- and UCSC disagree about exon structure, or the exon structure
-- changes between releases, the use of accession only becomes
-- ambiguous.
CREATE OR REPLACE VIEW _cds_exons_fp_v AS
SELECT DISTINCT SA.seq_id, md5(format('%s;%s',LOWER(SA.seq_id),CTEF.cds_se_i)) AS cds_es_fp, CTEF.*
  FROM _cds_exons_flat_v CTEF
  JOIN seq_anno SA ON CTEF.tx_ac=SA.ac;
