create view _discontiguous_tx as SELECT t.hgnc,
    es.exon_set_id,
    es.tx_ac,
    format('[%s-%s]'::text, e1.end_i, e2.start_i) AS gap,
    e1.exon_id AS e1_exon_id,
    e1.ord AS e1_ord,
    e1.start_i AS e1_start_i,
    e1.end_i AS e1_end_i,
    e2.exon_id AS e2_exon_id,
    e2.ord AS e2_ord,
    e2.start_i AS e2_start_i,
    e2.end_i AS e2_end_i
   FROM exon_set es
     LEFT JOIN transcript t ON es.tx_ac = t.ac
     JOIN exon e1 ON es.exon_set_id = e1.exon_set_id
     JOIN exon e2 ON es.exon_set_id = e2.exon_set_id AND e2.ord = (e1.ord + 1) AND e1.end_i <> e2.start_i
  WHERE es.alt_aln_method = 'transcript'::text;

