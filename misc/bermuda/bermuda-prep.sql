create materialized view ac_alts as
select tx_ac as ac,array_to_string(array_agg(alt_ac),',') as alts
from uta1.tx_aln_summary_mv
where alt_ac~'^NC_0000' and alt_aln_method='splign' group by tx_ac;

CREATE OR REPLACE VIEW nm_enst_equivalence_v AS 
SELECT N.tx_ac,array_agg(format('%s/C%s',E.tx_ac,CASE WHEN N.es_fingerprint=E.es_fingerprint THEN 'E' ELSE 'e' END)
	   							ORDER BY NOT N.es_fingerprint=E.es_fingerprint) as enst_equivs
FROM uta1.tx_def_summary_v N 
JOIN uta1.tx_def_summary_v E on N.cds_md5=E.cds_md5
WHERE N.tx_ac ~ '^NM_' and E.tx_ac ~ '^ENST'
GROUP BY N.tx_ac;
COMMENT ON VIEW nm_enst_equivalence_v IS 'RefSeq transcripts with ENST equivalence';

create or replace view splign_blat_equivalence_v as
select N.hgnc,N.tx_ac,N.alt_ac,
	   N.n_exons=U.n_exons as n_exons_eq,N.n_exons as splign_n_exons,U.n_exons as blat_n_exons,
	   N.se_i=U.se_i as se_i_eq,N.se_i as splign_se_i,U.se_i as blat_se_i
from uta1.tx_aln_summary_mv N
join uta1.tx_aln_summary_mv U on N.tx_ac=U.tx_ac and N.alt_aln_method='splign' and U.alt_aln_method='blat' and N.alt_ac=U.alt_ac;
COMMENT ON VIEW splign_blat_equivalence_v IS 'RefSeq transcripts with splign-blat equivalence';


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
from uta1.tx_exon_aln_v TEAS
join uta1.tx_exon_aln_v TEAB
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
