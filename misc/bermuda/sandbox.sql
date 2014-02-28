create materialized view alns_mv as
select distinct hgnc,split_part(tx_ac,'.',1) as tx_ac_b,tx_ac,alt_ac,alt_aln_method from uta1.tx_exon_aln_v WITH NO DATA;

create or replace view ealns_v as select * from alns_mv where tx_ac~'^NM_' and alt_ac~'^NC_0000';
create or replace view s_alns_v as select hgnc,tx_ac_b,tx_ac,alt_ac from ealns_v where alt_aln_method='splign';
create or replace view b_alns_v as select hgnc,tx_ac_b,tx_ac,alt_ac from ealns_v where alt_aln_method='blat';

CREATE OR REPLACE VIEW blat_splign_content_overlap as 
SELECT 
 'gene' as scope,
 (select count(*) from (select hgnc    from s_alns_v except    select hgnc    from b_alns_v) X) as splign,
 (select count(*) from (select hgnc    from s_alns_v intersect select hgnc    from b_alns_v) X) as both,
 (select count(*) from (select hgnc    from b_alns_v except    select hgnc    from s_alns_v) X) as blat
UNION ALL
SELECT 
 'base' as scope,
 (select count(*) from (select tx_ac_b from s_alns_v except    select tx_ac_b from b_alns_v) X) as splign,
 (select count(*) from (select tx_ac_b from s_alns_v intersect select tx_ac_b from b_alns_v) X) as both,
 (select count(*) from (select tx_ac_b from b_alns_v except    select tx_ac_b from s_alns_v) X) as blat
UNION ALL
SELECT 
 'ac' as scope,
 (select count(*) from (select tx_ac   from s_alns_v except    select tx_ac   from b_alns_v) X) as splign,
 (select count(*) from (select tx_ac   from s_alns_v intersect select tx_ac   from b_alns_v) X) as both,
 (select count(*) from (select tx_ac   from b_alns_v except    select tx_ac   from s_alns_v) X) as blat
;



-- other stuff
drop view if exists tx_3way_v;
create or replace view tx_3way_v as
select T.hgnc,T.ac,ESS.alt_ac,ET.ord,
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
from uta1.transcript T
left join uta1.exon_set EST on T.ac=EST.tx_ac and EST.alt_aln_method='transcript'
left join uta1.exon_set ESS on T.ac=ESS.tx_ac and ESS.alt_aln_method='splign'
left join uta1.exon_set ESB on T.ac=ESB.tx_ac and ESB.alt_aln_method='blat' and ESS.alt_ac=ESB.alt_ac
left join uta1.exon ET on EST.exon_set_id=ET.exon_set_id
left join uta1.exon ES on ESS.exon_set_id=ES.exon_set_id and ET.ord=ES.ord
left join uta1.exon EB on ESB.exon_set_id=EB.exon_set_id and ET.ord=EB.ord
left join uta1.exon_aln EATS on ET.exon_id=EATS.tx_exon_id and ES.exon_id=EATS.alt_exon_id
left join uta1.exon_aln EATB on ET.exon_id=EATB.tx_exon_id and EB.exon_id=EATB.alt_exon_id
where T.ac ~ '^NM_';



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




