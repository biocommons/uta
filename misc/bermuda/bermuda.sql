-- Transcript comparison, aka the infamous "Bermuda doc"
-- see Bermuda.txt for background


-- ############################################################################
-- ## UTA0 (t=transcript, gs=genomic splign)
create or replace view u0_t_exons_v as 
select ac,count(*) as u0_t_n_exons,
	   array_to_string(array_agg(format('%s,%s',start_i,end_i) order by ord),';') as u0_t_se_i,
	   array_to_string(array_agg(end_i-start_i order by ord),';') as u0_t_lengths
from uta0.transcript_exon
group by ac;

create or replace view u0_gs_exons_v as 
select GE.ac,G.strand as u0_strand,count(*) as u0_gs_n_exons,
	   array_to_string(array_agg(format('%s,%s',GE.start_i,GE.end_i) order by ord),';') as u0_gs_se_i,
	   array_to_string(array_agg(GE.end_i-GE.start_i order by ord),';') as u0_gs_lengths 
from uta0.genomic_exon GE
join uta0.transcript T on GE.ac=T.ac
join uta0.gene G on T.gene=G.gene
group by GE.ac,G.strand;

create or replace view u0_tgs_summary_v as
select TES.ac,aln_status(u0_t_se_i,u0_gs_se_i,u0_to_u1_cigar(TGA.cigars)) as u0_tgs_status,GES.u0_strand,u0_t_n_exons,u0_t_se_i,u0_t_lengths,u0_gs_n_exons,u0_gs_se_i,u0_gs_lengths,u0_to_u1_cigar(TGA.cigars) as u0_tgs_cigars
from u0_t_exons_v as TES
left join u0_gs_exons_v GES on TES.ac=GES.ac
left join uta0.transcript_cigars_v TGA on TES.ac=TGA.ac;


-- ############################################################################
-- ## UTA1 (t=transcript, gs=genomic splign, gb=genomic blat)
create or replace view u1_t_exons_v as
select tx_ac as ac,n_exons as u1_t_n_exons,se_i as u1_t_se_i,array_to_string(lengths,';') as u1_t_lengths
from uta1.tx_def_summary_v;

create or replace view u1_gs_exons_v as 
select tx_ac as ac,alt_strand as u1_gs_strand,n_exons as u1_gs_n_exons,se_i as u1_gs_se_i,array_to_string(lengths,';') as u1_gs_lengths
from uta1.tx_aln_summary_v
where alt_ac~'^NC_0000' and alt_aln_method='splign';

create or replace view u1_tgs_summary_v as
select TES.ac,aln_status(u1_t_se_i,u1_gs_se_i,cigars) as u1_tgs_status,GES.u1_gs_strand,u1_t_n_exons,u1_t_se_i,u1_t_lengths,u1_gs_n_exons,u1_gs_se_i,u1_gs_lengths,TGA.cigars as u1_tgs_cigars
from u1_t_exons_v as TES
left join u1_gs_exons_v GES on TES.ac=GES.ac
left join uta1.tx_aln_cigar_mv TGA on TES.ac=TGA.tx_ac
where TGA.alt_ac~'^NC_0000' and TGA.alt_aln_method='splign';

create or replace view u1_gb_exons_v as 
select tx_ac as ac,alt_strand as u1_gb_strand,n_exons as u1_gb_n_exons,se_i as u1_gb_se_i,array_to_string(lengths,';') as u1_gb_lengths
from uta1.tx_aln_summary_v
where alt_ac~'^NC_0000' and alt_aln_method='blat';

create or replace view u1_tgb_summary_v as
select TES.ac,aln_status(u1_t_se_i,u1_gb_se_i,cigars) as u1_tgb_status,GES.u1_gb_strand,u1_t_n_exons,u1_t_se_i,u1_t_lengths,u1_gb_n_exons,u1_gb_se_i,u1_gb_lengths,TGA.cigars as u1_tgb_cigars
from u1_t_exons_v as TES
left join u1_gb_exons_v GES on TES.ac=GES.ac
left join uta1.tx_aln_cigar_mv TGA on TES.ac=TGA.tx_ac
where TGA.alt_ac~'^NC_0000' and TGA.alt_aln_method='blat';


create or replace view u01_v as 
select T.hgnc, AA.alts, u0.ac, u0.u0_strand,
	   u0.u0_tgs_status, u1.u1_tgs_status,

	   u0.u0_t_n_exons, u1.u1_t_n_exons,
	   u0.u0_gs_n_exons, u1.u1_gs_n_exons,

	   u0.u0_t_lengths, u1.u1_t_lengths,
	   u0.u0_gs_lengths, u1.u1_gs_lengths,

	   u0.u0_t_se_i, u1.u1_t_se_i, 
	   u0.u0_gs_se_i, u1.u1_gs_se_i,

	   u0.u0_tgs_cigars, u1.u1_tgs_cigars

from u0_tgs_summary_v as u0
join u1_tgs_summary_v u1 on u0.ac=u1.ac
left join ac_alts AA on u0.ac=AA.ac
left join uta1.transcript T on u0.ac=T.ac
;

create materialized view u01_mv as select * from u01_v WITH NO DATA;


create or replace view u1sb_v as 
select T.hgnc, AA.alts, u1s.ac, u1s.u1_gs_strand,
	   u1s.u1_tgs_status, u1b.u1_tgb_status,

	   u1s.u1_t_n_exons,
	   u1s.u1_gs_n_exons, u1b.u1_gb_n_exons,

	   u1s.u1_t_lengths,
	   u1s.u1_gs_lengths, u1b.u1_gb_lengths,

	   u1s.u1_t_se_i,
	   u1s.u1_gs_se_i, u1b.u1_gb_se_i,

	   u1s.u1_tgs_cigars, u1b.u1_tgb_cigars

from u1_tgs_summary_v as u1s
join u1_tgb_summary_v u1b on u1s.ac=u1b.ac
left join ac_alts AA on u1s.ac=AA.ac
left join uta1.transcript T on u1s.ac=T.ac
;


create materialized view u1sb_mv as select * from u1sb_v WITH NO DATA;



create or replace view bermuda_data_dv as
select TDS.hgnc, 
	   GSP.ck_release as ck, GSP.acmg_mr as acmg, GSP.htd,
	   TDS.tx_ac,TASS.alt_ac,
	   TASS.alt_strand,TDS.n_exons,
	   aln_status(TDS.se_i,TASS.se_i,TASS.cigars) = 'NLxdi' as s_refagree,
	   aln_status(TDS.se_i,TASB.se_i,TASB.cigars) = 'NLxdi' as b_refagree,
	   aln_status(TDS.se_i,TASS.se_i,TASS.cigars) = aln_status(TDS.se_i,TASB.se_i,TASB.cigars) as sb_status_eq,
	   TASS.se_i = TASB.se_i as sb_se_i_eq,
	   aln_status(TDS.se_i,TASS.se_i,TASS.cigars) as s_status,
	   aln_status(TDS.se_i,TASB.se_i,TASB.cigars) as b_status,
	   cigar_stats_is_trivial(TASSCS) as s_trivial,
	   cigar_stats_is_trivial(TASBCS) as b_trivial,
	   (case when max_abs_sb_start_diff>max_abs_sb_end_diff then max_abs_sb_start_diff else max_abs_sb_end_diff end) as max_coord_diff,
	   NEE.enst_equivs,
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
left join nm_enst_equivalence_v NEE on TDS.tx_ac=NEE.tx_ac
left join splign_blat_equivalence_v SBE on TASS.tx_ac=SBE.tx_ac and TASS.alt_ac=SBE.alt_ac
left join gene_set_pivot_v GSP on TDS.hgnc=GSP.hgnc
where TDS.tx_ac ~ '^NM_'
order by hgnc,tx_ac,alt_ac;


create materialized view bermuda_data_mv as select * from bermuda_data_dv WITH NO DATA;
grant select on bermuda_data_mv to public;


create or replace view bermuda_data_pivot_v as
select transcript_class(sb_se_i_eq, sb_status_eq, s_refagree, b_refagree, s_trivial, b_trivial),*
from (
	   select sb_se_i_eq,sb_status_eq,s_refagree,b_refagree,s_trivial,b_trivial,
	   round(avg(max_coord_diff)) as avg_max_coord_diff,
	   count(*) as n,
	   count(distinct tx_ac) as n_tx_ac,
	   count(distinct B.hgnc) as n_hgnc,
	   coalesce(sum(case when ck then 1 else 0 end),0) as ck,
	   coalesce(sum(case when acmg then 1 else 0 end),0) as acmg,
	   coalesce(sum(case when htd then 1 else 0 end),0) as htd
	   from bermuda_data_mv B
	   group by sb_se_i_eq,sb_status_eq,s_refagree,b_refagree,s_trivial,b_trivial
) X
order by 1,2,3,4,5,6,7;
;
