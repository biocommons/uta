drop view gene_summary_v;

CREATE OR REPLACE VIEW gene_summary_v AS
SELECT GI.gene,GI.maploc,GI.g_coord,GS.n_NMs,GS.n_NM_refagree,GS.n_NM_sub,GS.n_NM_indel,GS.n_enst_eq,GS.n_nm_exact,GS.n_nm_base
  FROM (SELECT DISTINCT ON (gene) gene,maploc,format('%s%s:%s-%s',CASE strand WHEN -1 THEN '-' ELSE '+' END,chr,start_i+1,end_i+1) AS g_coord
        FROM transcript_table_mv) GI
	
   JOIN (SELECT gene,
         count(ac) as n_NMs,
         sum(case when status = 'NLxdi' then 1 else 0 end) as n_NM_refagree, 
         sum(case when status ~ 'X' then 1 else 0 end) as n_NM_sub,
         sum(case when status ~ '[DI]' then 1 else 0 end) as n_NM_indel,
 
         sum(case when enst_equivs is not null then 1 else 0 end) as n_enst_eq,
         sum(case when ac = e_refseq_ac then 1 else 0 end) as n_nm_exact,
         sum(case when split_part(ac,'.',1) = split_part(e_refseq_ac,'.',1) then 1 else 0 end) as n_nm_base
 
 		FROM transcript_table_mv
 		group by gene) GS 
   ON GI.gene = GS.gene

;
