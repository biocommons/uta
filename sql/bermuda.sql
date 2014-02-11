-- Transcript comparison, aka the infamous "Bermuda doc"
-- see Bermuda.txt for background


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


create or replace view bermuda_v as
select TDS.hgnc,TDS.tx_ac,TASS.alt_ac,TASS.alt_strand,TDS.n_exons,
	   aln_status(TDS.se_i,TASS.se_i,TASS.cigars) = 'NLxdi' as s_refagree,
	   aln_status(TDS.se_i,TASB.se_i,TASB.cigars) = 'NLxdi' as b_refagree,
	   aln_status(TDS.se_i,TASS.se_i,TASS.cigars) = aln_status(TDS.se_i,TASB.se_i,TASB.cigars) as sb_status_eq,
	   TASS.se_i = TASB.se_i as sb_se_i_eq,
	   aln_status(TDS.se_i,TASS.se_i,TASS.cigars) as s_status,
	   aln_status(TDS.se_i,TASB.se_i,TASB.cigars) as b_status,
	   cigar_stats(TASS.cigars) as s_cigar_stats,
	   cigar_stats(TASB.cigars) as b_cigar_stats,
	   NEE.enst_equivs,
	   TASS.se_i as s_se_i,
	   TASB.se_i as b_se_i,
	   sv_cmp(';',TASS.se_i,TASB.se_i) as sb_se_i_cmp,
	   TASS.cigars as s_cigars,
	   TASB.cigars as b_cigars,
	   sv_cmp(',',TASS.cigars,TASB.cigars) as sb_cigar_cmp
from tx_def_summary_v TDS
join tx_aln_summary_mv TASS on TDS.tx_ac=TASS.tx_ac and TASS.alt_aln_method='splign'
join tx_aln_summary_mv TASB on TASS.tx_ac=TASB.tx_ac and TASS.alt_ac=TASB.alt_ac and TASB.alt_aln_method='blat'
left join nm_enst_equivalence_v NEE on TDS.tx_ac=NEE.tx_ac
left join splign_blat_equivalence_v SBE on TASS.tx_ac=SBE.tx_ac and TASS.alt_ac=SBE.alt_ac
where TASS.alt_ac ~ '^NC_0000'	-- ~ GRCh37 primary assy
order by hgnc,tx_ac,alt_ac;
comment on view bermuda_v is 'the infamous bermuda doc!';

create materialized view bermuda_mv as select * from bermuda_v;
create view bermuda_pivot as select sb_se_i_eq,sb_status_eq,s_refagree,b_refagree,count(*) as n, count(distinct tx_ac) as n_tx_ac,count(distinct hgnc) as n_hgnc from bermuda_mv group by 1,2,3,4;
grant select on bermuda_mv to public;


create or replace view exon_alignments_v as
select TES.exon_set_id as tes_exon_set_id,AES.exon_set_id as aes_exon_set_id,
	   TES.tx_ac as tx_ac,AES.alt_ac as alt_ac,AES.alt_strand,AES.alt_aln_method,
	   TEX.ord as ord,TEX.exon_id as tx_exon_id,AEX.exon_id as alt_exon_id,
	   TEX.start_i as tx_start_i,TEX.end_i as tx_end_i, AEX.start_i as alt_start_i,AEX.end_i as alt_end_i,
	   EA.cigar
from exon_set TES
join exon_set AES on TES.tx_ac=AES.tx_ac and TES.alt_aln_method='transcript' and AES.alt_aln_method!='transcript'
join exon TEX on TES.exon_set_id=TEX.exon_set_id
join exon AEX on AES.exon_set_id=AEX.exon_set_id and TEX.ord=AEX.ord
left join exon_aln EA on EA.tx_exon_id=TEX.exon_id and EA.alt_exon_id=AEX.exon_id;


create view bermuda_pivot_v as select sb_se_i_eq,sb_status_eq,s_refagree,b_refagree,
	   count(*) as n, count(distinct tx_ac) as n_tx_ac,count(distinct hgnc) as n_hgnc
from bermuda_mv
group by 1,2,3,4;
