CREATE OR REPLACE VIEW genomic_exons_flat_v AS
SELECT ac,COUNT(ord) as n_exons,
       array_to_string(array_agg(start_i order by ord),',') as starts_i,
       array_to_string(array_agg(end_i order by ord),',') as ends_i,
       array_to_string(array_agg(end_i-start_i order by ord),',') as lengths
FROM genomic_exon
GROUP BY ac;

CREATE OR REPLACE VIEW transcript_exons_flat_v AS
SELECT ac,COUNT(ord) as n_exons,
       array_to_string(array_agg(start_i order by ord),',') as starts_i,
       array_to_string(array_agg(end_i order by ord),',') as ends_i,
       array_to_string(array_agg(end_i-start_i order by ord),',') as lengths
FROM transcript_exon
GROUP BY ac;

CREATE OR REPLACE VIEW transcript_cigars_v AS
SELECT T.ac,
       array_to_string(array_agg(GA.cigar order by TE.ord),',') as cigars
FROM transcript T
JOIN genomic_exon GE on T.ac=GE.ac
JOIN transcript_exon TE on GE.ac=TE.ac
JOIN gtx_alignment GA on (GE.genomic_exon_id=GA.genomic_exon_id 
                      and TE.transcript_exon_id=GA.transcript_exon_id)
GROUP BY T.ac;


CREATE OR REPLACE VIEW exon_alignments_v AS
SELECT G.gene,T.ac,TE.ord,TE.name,
       TE.end_i-TE.start_i as t_ex_len,GE.end_i-GE.start_i as g_ex_len,GA.cigar
FROM gene G
JOIN transcript T on G.gene=T.gene
JOIN genomic_exon GE on T.ac=GE.ac
JOIN transcript_exon TE on T.ac=TE.ac
JOIN gtx_alignment GA on (GE.genomic_exon_id=GA.genomic_exon_id 
                         and TE.transcript_exon_id=GA.transcript_exon_id)
ORDER BY gene,ac,ord;


CREATE OR REPLACE VIEW transcript_discrepancies_v AS
SELECT T.gene, GE.ac,
       array_to_string(array_agg(GA.cigar order by TE.ord),',') as cigars,
       array_to_string(array_agg(GA.seqviewer_url order by TE.ord),',') as seqviewer_urls
FROM genomic_exon GE
JOIN transcript_exon TE on GE.ac=TE.ac
JOIN transcript T on TE.ac = T.ac
JOIN gtx_alignment GA on (GE.genomic_exon_id=GA.genomic_exon_id 
                         and TE.transcript_exon_id=GA.transcript_exon_id)
WHERE GA.cigar ~ '[DIX]'
GROUP BY T.gene, GE.ac;



CREATE OR REPLACE VIEW transcript_summary_v AS
SELECT G.gene,T.ac,TEF.n_exons as n_t_exons,GEF.n_exons as n_g_exons,
       CONCAT(
        CASE WHEN TEF.n_exons=GEF.n_exons THEN 'N' ELSE 'n' END,
        CASE WHEN TEF.lengths=GEF.lengths THEN 'L' ELSE 'l' END,
        CASE WHEN TC.cigars !~ 'X' 		  THEN 'x' ELSE 'X' END,
        CASE WHEN TC.cigars !~ 'D' 		  THEN 'd' ELSE 'D' END,
        CASE WHEN TC.cigars !~ 'I' 		  THEN 'i' ELSE 'I' END
        ) as status,
        TEF.lengths,TC.cigars,TD.seqviewer_urls
FROM transcript T
JOIN gene G on T.gene=G.gene
LEFT JOIN transcript_exons_flat_v TEF on T.ac=TEF.ac
LEFT JOIN genomic_exons_flat_v GEF on T.ac=GEF.ac
LEFT JOIN transcript_cigars_v TC on T.ac=TC.ac
LEFT JOIN transcript_discrepancies_v TD on T.ac=TD.ac
;


CREATE OR REPLACE VIEW nm_enst_equivs_v AS
SELECT ac,
       array_to_string(array_agg(concat(enst,'/',status) order by status desc),',') as enst_equivs
FROM nm_enst_equiv
WHERE status in ('CE','CC')
GROUP BY ac;


CREATE OR REPLACE VIEW transcript_table_v AS
SELECT G.gene, G.maploc, G.chr, G.strand, G.start_i, G.end_i,
	   T.ac, T.cds_start_i, T.cds_end_i,
       TS.status, TS.n_t_exons, TS.n_g_exons, 
	   TS.lengths, TS.cigars, TS.seqviewer_urls,
	   NEE.ac as e_refseq_ac, NEE.enst_equivs
FROM gene G
JOIN transcript T on G.gene=T.gene
LEFT JOIN transcript_summary_v TS on T.ac=TS.ac
LEFT JOIN nm_enst_equivs_v NEE on split_part(T.ac,'.',1)=split_part(NEE.ac,'.',1);



CREATE OR REPLACE VIEW transcript_cds_exon_v AS
SELECT transcript_exon_id,TE.ac,
	   greatest(TE.start_i,T.cds_start_i) as start_i,
	   least(TE.end_i,T.cds_end_i) as end_i,
	   ord, name
FROM transcript_exon TE
JOIN transcript T ON TE.ac=T.ac
WHERE TE.start_i <= T.cds_end_i AND TE.end_i >= T.cds_start_i
;



CREATE OR REPLACE VIEW genome_transcript_exon_pairs as
SELECT GE.genomic_exon_id,TE.transcript_exon_id,
  G.gene,T.ac,
  G.chr,G.strand,GE.start_i as g_start_i,GE.end_i as g_end_i,
  TE.start_i as t_start_i,TE.end_i as t_end_i,
  TE.ord, TE.name
FROM gene G
LEFT JOIN transcript T on G.gene=T.gene
LEFT JOIN genomic_exon GE on T.ac=GE.ac
LEFT JOIN transcript_exon TE on GE.ac=TE.ac and GE.ord=TE.ord
;


CREATE OR REPLACE VIEW exon_n_mismatch AS
SELECT TEF.ac,TEF.n_exons as n_t_exons,GEF.n_exons as n_g_exons,
	   TEF.lengths as t_lengths,GEF.lengths as g_lengths
FROM transcript_exons_flat_v TEF
JOIN genomic_exons_flat_v GEF ON TEF.ac=GEF.ac
WHERE TEF.n_exons!=GEF.n_exons
;
