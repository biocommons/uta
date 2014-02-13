-- select * from sbdiff_stats_mv where max_abs_sb_start_diff > 5 and max_abs_sb_end_diff > 5 and n_mismatch > 0  order by hgnc,tx_ac;
-- 


create or replace view sbdiff_v as
select TEAS.hgnc,TEAS.tx_ac,TEAS.alt_ac,TEAS.alt_strand,TEAS.ord,
	   TEAS.tx_start_i,TEAS.tx_end_i,
	   TEAS.alt_start_i as s_start_i,TEAS.alt_end_i as s_end_i,
	   TEAB.alt_start_i as b_start_i,TEAB.alt_end_i as b_end_i,
	   TEAS.alt_start_i - TEAB.alt_start_i as sb_start_diff,
	   TEAS.alt_end_i   - TEAB.alt_end_i as sb_end_diff,
	   TEAS.tx_end_i - TEAS.tx_start_i as s_len,
	   TEAB.alt_end_i - TEAB.alt_start_i as b_len,
	   TEAS.cigar as s_cigar,
	   TEAB.cigar as b_cigar
from tx_exon_aln_v TEAS
join tx_exon_aln_v TEAB
	 on TEAS.tx_ac=TEAB.tx_ac 
	 and TEAS.alt_ac=TEAB.alt_ac
	 and TEAS.ord=TEAB.ord
	 and TEAS.alt_aln_method='splign'
	 and TEAB.alt_aln_method='blat'
;


create or replace view sbdiff_stats_dv as
select hgnc,tx_ac,alt_ac,
	   count(*) as n_exon,
	   sum(case when sb_start_diff>0 or sb_end_diff>0 then 1 else 0 end) as n_mismatch,
	   round(avg(abs(sb_start_diff))) as avg_abs_sb_start_diff,
	   max(abs(sb_start_diff)) as max_abs_sb_start_diff,
	   round(avg(abs(sb_end_diff))) as avg_abs_sb_end_diff,
	   max(abs(sb_end_diff)) as max_abs_sb_end_diff
from sbdiff_v
group by hgnc,tx_ac,alt_ac;


create materialized view sbdiff_stats_mv as select * from sbdiff_stats_dv WITH NO DATA;

-- then: refresh materialized view sbdiff_stats_mv ;
