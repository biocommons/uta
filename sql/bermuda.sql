-- Transcript comparison, aka the infamous "Bermuda doc"
-- see Bermuda.txt for background


drop view tx_3way_v;
create or replace view tx_3way_v as
select T.hgnc,T.ac,EST.alt_ac,ET.ord,
	   (ET.end_i-ET.start_i) - (ES.end_i-ES.start_i) as ts_len_diff,
	   (ET.end_i-ET.start_i) - (EB.end_i-EB.start_i) as tb_len_diff,
	   (ES.start_i - EB.start_i) as sb_start_i_diff,
	   (ES.end_i - EB.end_i) as sb_end_i_diff,
	   ET.start_i as t_start_i,ET.end_i as t_end_i,ET.end_i-ET.start_i as t_len,
	   ES.start_i as s_start_i,ES.end_i as s_end_i,ES.end_i-ES.start_i as s_len,
	   EB.start_i as b_start_i,EB.end_i as b_end_i,EB.end_i-EB.start_i as b_len,
	   EATS.cigar as ts_cigar, EATB.cigar as tb_cigar,
	   EST.exon_set_id as t_exon_set_id, ESS.exon_set_id as s_exon_set_id, ESB.exon_set_id as b_exon_set_id,
	   ET.exon_id as t_exon_id,ES.exon_id as s_exon_id,EB.exon_id as b_exon_id,
	   EATS.exon_aln_id as ts_exon_aln_id, EATB.exon_aln_id as tb_exon_aln_id
from transcript T
left join exon_set EST on T.ac=EST.tx_ac and EST.alt_aln_method='transcript'
left join exon_set ESS on T.ac=ESS.tx_ac and ESS.alt_aln_method='splign'
left join exon_set ESB on T.ac=ESB.tx_ac and ESB.alt_aln_method='blat' and ESS.alt_ac=ESB.alt_ac
left join exon ET on EST.exon_set_id=ET.exon_set_id
left join exon ES on ESS.exon_set_id=ES.exon_set_id and ET.ord=ES.ord
left join exon EB on ESB.exon_set_id=EB.exon_set_id and ET.ord=EB.ord
left join exon_aln EATS on ET.exon_id=EATS.tx_exon_id and ES.exon_id=EATS.alt_exon_id
left join exon_aln EATB on ET.exon_id=EATB.tx_exon_id and EB.exon_id=EATB.alt_exon_id
where T.ac ~ '^NM_';
;


CREATE OR REPLACE VIEW nm_enst_equivalence_v AS 
SELECT N.tx_ac,array_agg(format('%s/C%s',E.tx_ac,CASE WHEN N.es_fingerprint=E.es_fingerprint THEN 'E' ELSE 'e' END) ORDER BY NOT N.es_fingerprint=E.es_fingerprint) as enst_equivs
FROM tx_def_summary_v N 
JOIN tx_def_summary_v E on N.cds_md5=E.cds_md5
WHERE N.tx_ac ~ '^NM_' and E.tx_ac ~ '^ENST'
GROUP BY N.tx_ac;
COMMENT ON VIEW nm_enst_equivalence_v IS 'RefSeq transcripts with ENST equivalence';

create or replace view splign_blat_equivalence_v as
select N.hgnc,N.tx_ac,N.alt_ac,
	   N.n_exons=U.n_exons as n_exons_eq,N.n_exons as splign_n_exons,U.n_exons as blat_n_exons,
	   N.se_i=U.se_i as se_i_eq,N.se_i as splign_se_i,U.se_i as blat_se_i
from tx_aln_summary_mv N
join tx_aln_summary_mv U on N.tx_ac=U.tx_ac and N.alt_aln_method='splign' and U.alt_aln_method='blat' and N.alt_ac=U.alt_ac;
COMMENT ON VIEW splign_blat_equivalence_v IS 'RefSeq transcripts with splign-blat equivalence';

create or replace view bermuda_dv as
select TDS.hgnc,TDS.tx_ac,TASS.alt_ac,
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
from tx_def_summary_v TDS
join tx_aln_summary_mv TASS on TDS.tx_ac=TASS.tx_ac and TASS.alt_aln_method='splign'
join tx_aln_summary_mv TASB on TASS.tx_ac=TASB.tx_ac and TASS.alt_ac=TASB.alt_ac and TASB.alt_aln_method='blat'
join cigar_stats(TASS.cigars) as TASSCS on True
join cigar_stats(TASB.cigars) as TASBCS on True
join sbdiff_stats_mv SBDS on TDS.tx_ac=SBDS.tx_ac and TASS.alt_ac=SBDS.alt_ac
left join nm_enst_equivalence_v NEE on TDS.tx_ac=NEE.tx_ac
left join splign_blat_equivalence_v SBE on TASS.tx_ac=SBE.tx_ac and TASS.alt_ac=SBE.alt_ac
where TASS.alt_ac ~ '^NC_0000'	-- ~ GRCh37 primary assy
order by hgnc,tx_ac,alt_ac;
comment on view bermuda_dv is 'the infamous bermuda doc!';


create materialized view bermuda_mv as select * from bermuda_dv WITH NO DATA;
grant select on bermuda_mv to public;




create or replace view bermuda_pivot_v as
	   select sb_se_i_eq,sb_status_eq,s_refagree,b_refagree,s_trivial,b_trivial,
	   round(avg(max_coord_diff)) as avg_max_coord_diff,count(*) as n, count(distinct tx_ac) as n_tx_ac,count(distinct hgnc) as n_hgnc
from bermuda_mv
group by sb_se_i_eq,sb_status_eq,s_refagree,b_refagree,s_trivial,b_trivial
order by sb_se_i_eq,sb_status_eq,s_refagree,b_refagree,s_trivial,b_trivial
;
