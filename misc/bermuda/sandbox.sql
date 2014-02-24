set search_path = sandbox;
create materialized view alns_mv as select distinct hgnc,split_part(tx_ac,'.',1) as tx_ac_b,tx_ac,alt_ac,alt_aln_method from uta1.tx_exon_aln_v;
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
