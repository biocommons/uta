create or replace view bermuda_data_dv as
select TDS.hgnc, 
	   GSP.ck_release as ck, GSP.acmg_mr as acmg, GSP.htd,
	   exists(select * from hgmd_gene_transcripts HGT where TDS.hgnc=HGT.hgnc and TDS.tx_ac=HGT.ac) as is_hgmd_tx,
	   TDS.tx_ac, TDS.cds_start_i, TDS.cds_end_i,
	   TASS.alt_ac, TASS.alt_strand, regexp_replace(TASS.se_i,',.+,','-') as "alt_coords",
	   P.patches,
	   TDS.n_exons,
	   aln_status(TDS.se_i,TASS.se_i,TASS.cigars) = 'NLxdi' as s_refagree,
	   aln_status(TDS.se_i,TASB.se_i,TASB.cigars) = 'NLxdi' as b_refagree,
	   aln_status(TDS.se_i,TASS.se_i,TASS.cigars) = aln_status(TDS.se_i,TASB.se_i,TASB.cigars) as sb_status_eq,
	   TASS.se_i = TASB.se_i as sb_se_i_eq,
	   aln_status(TDS.se_i,TASS.se_i,TASS.cigars) as s_status,
	   aln_status(TDS.se_i,TASB.se_i,TASB.cigars) as b_status,
	   cigar_stats_is_minor(TASSCS) as s_minor,
	   cigar_stats_is_minor(TASBCS) as b_minor,
	   (case when max_abs_sb_start_diff>max_abs_sb_end_diff then max_abs_sb_start_diff else max_abs_sb_end_diff end) as max_coord_diff,
	   NEEF.enst_equivs,
	   TDS.se_i as t_se_i,
	   array_to_string(TDS.lengths,';') as t_lengths,
	   TASS.se_i as s_se_i,
	   TASB.se_i as b_se_i,
	   sv_cmp(';',TASS.se_i,TASB.se_i) as sb_se_i_cmp,
	   TASS.cigars as s_cigars,
	   TASB.cigars as b_cigars,
	   sv_cmp(',',TASS.cigars,TASB.cigars) as sb_cigar_cmp,
	   TASSCS.collapsed_cigar as s_collapsed_cigar,TASSCS.l1 as s_l1,TASSCS.l2 as s_l2,TASSCS.n_ex as s_n_ex,TASSCS.n_ops as s_n_ops,TASSCS.n_e as s_n_e,TASSCS.n_x as s_n_x,TASSCS.n_d as s_n_d,TASSCS.n_i as s_n_i,TASSCS.t_e as s_t_e,TASSCS.t_x as s_t_x,TASSCS.t_d as s_t_d,TASSCS.t_i as s_t_i,
	   TASBCS.collapsed_cigar as b_collapsed_cigar,TASBCS.l1 as b_l1,TASBCS.l2 as b_l2,TASBCS.n_ex as b_n_ex,TASBCS.n_ops as b_n_ops,TASBCS.n_e as b_n_e,TASBCS.n_x as b_n_x,TASBCS.n_d as b_n_d,TASBCS.n_i as b_n_i,TASBCS.t_e as b_t_e,TASBCS.t_x as b_t_x,TASBCS.t_d as b_t_d,TASBCS.t_i as b_t_i
from uta1.tx_def_summary_v TDS
full join uta1.tx_aln_summary_mv TASS on TDS.tx_ac=TASS.tx_ac and TASS.alt_ac ~ '^NC_0000' and TASS.alt_aln_method='splign'
full join uta1.tx_aln_summary_mv TASB on TDS.tx_ac=TASB.tx_ac and TASB.alt_ac ~ '^NC_0000' and TASB.alt_aln_method='blat'
left join cigar_stats(TASS.cigars) as TASSCS on True
left join cigar_stats(TASB.cigars) as TASBCS on True
left join sbdiff_stats_mv SBDS on TDS.tx_ac=SBDS.tx_ac and TASS.alt_ac=SBDS.alt_ac
left join nm_enst_equivs_flat NEEF on TDS.tx_ac=NEEF.nm
left join gene_set_pivot_v GSP on TDS.hgnc=GSP.hgnc
left join (
	 select tx_ac,string_agg(distinct alt_ac,',' order by alt_ac) as patches
	 from exon_set
	 where tx_ac ~ '^NM_' and alt_ac ~ '^NW_'
	 group by tx_ac
	 ) P on TDS.tx_ac=P.tx_ac
where TDS.tx_ac ~ '^NM_'
order by hgnc,tx_ac,alt_ac;


create materialized view bermuda_data_mv as select * from bermuda_data_dv WITH NO DATA;
grant select on bermuda_data_mv to public;
