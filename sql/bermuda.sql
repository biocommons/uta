-- Transcript comparison, aka the infamous "Bermuda doc"
-- see Bermuda.txt for background


create or replace view exon_set_exons_dv as
select ES.*,EL.n_exons,EL.se_i,EL.starts_i,EL.ends_i,EL.lengths
from exon_set ES
join (select 
  iES.exon_set_id,
  count(*) as n_exons,
  array_to_string(array_agg(format('%s,%s',iE.start_i,iE.end_i) order by iE.ord),';') as se_i,
  array_agg(iE.start_i            order by iE.ord) as starts_i,
  array_agg(iE.end_i              order by iE.ord) as ends_i,
  array_agg((iE.end_i-iE.start_i) order by iE.ord) as lengths
  from exon_set iES
  join exon iE on iES.exon_set_id=iE.exon_set_id
  group by iES.exon_set_id) EL
  on ES.exon_set_id = EL.exon_set_id;
comment on view exon_set_exons_dv is 'defining view of "flat" (aggregated) exons on a sequence; use _mv; for faster materialized version';


create table exon_set_exons_mv as select * from exon_set_exons_dv;
comment on table exon_set_exons_mv is 'materialized view of "flat" (aggregated) exons on a sequence; also see _dv form for view definition';


create or replace view  exon_set_exons_fp_dv as
select ESE.*,md5(format('%s;%s',lower(ASA.seq_id),ESE.se_i)) as es_fingerprint
from exon_set_exons_mv ESE
join seq_anno ASA on ESE.alt_ac=ASA.ac;
comment on view exon_set_exons_fp_v is 'defining view of exon_set_exons_mv + exon set fingerprint';


create table exon_set_exons_fp_mv as select * from exon_set_exons_fp_dv;
comment on table exon_set_exons_fp_mv is 'materialized view of "flat" (aggregated) exons on a sequence with fingerprint; also see _dv form for view definition';


-- ideally, we'd include cds start and end here, but we don't yet map CDS
-- start and end to alt exon.  This are simple offsets in most cases,
-- except when there are indels, which is why I'm not doing that now.
create or replace view tx_def_summary_v as
select T.hgnc,T.cds_md5,exon_set_id,tx_ac,ESE.added,n_exons,se_i,starts_i,ends_i,lengths,es_fingerprint from transcript T
join exon_set_exons_fp_mv ESE on T.ac=ESE.tx_ac
where ESE.alt_aln_method = 'transcript';
comment on view tx_def_summary_v is 'transcript definitions, with exon structures';


create or replace view tx_aln_cigar_dv as
select AES.tx_ac,AES.alt_ac,AES.alt_strand,AES.alt_aln_method,
	   count(*) as n_exons, string_agg(EA.cigar,','  order by TEX.ord) as cigars
from exon_set TES
join exon_set AES on TES.tx_ac=AES.tx_ac and TES.alt_aln_method='transcript' and AES.alt_aln_method!='transcript'
join exon TEX on TES.exon_set_id=TEX.exon_set_id
join exon AEX on AES.exon_set_id=AEX.exon_set_id and TEX.ord=AEX.ord
join exon_aln EA on EA.tx_exon_id=TEX.exon_id and EA.alt_exon_id=AEX.exon_id
group by AES.tx_ac,AES.alt_ac,AES.alt_strand,AES.alt_aln_method;


create table tx_aln_cigar_mv as select * from tx_aln_cigar_dv;


create or replace view tx_aln_summary_dv as
select T.hgnc,T.cds_md5,ESE.*,TAC.cigars from transcript T
join exon_set_exons_fp_mv ESE on T.ac=ESE.tx_ac
left join tx_aln_cigar_mv TAC on ESE.tx_ac=TAC.tx_ac and ESE.alt_ac=TAC.alt_ac and ESE.alt_aln_method=TAC.alt_aln_method
where ESE.alt_aln_method != 'transcript';
comment on view tx_def_summary_v is 'transcript alignments on alternate seqeuences, with exon structures';


create table tx_aln_summary_mv as select * from tx_aln_summary_dv;


CREATE OR REPLACE VIEW nm_enst_equivalence_v AS 
SELECT N.tx_ac,array_agg(format('%s/C%s',E.tx_ac,CASE WHEN N.es_fingerprint=E.es_fingerprint THEN 'E' ELSE 'e' END) ORDER BY NOT N.es_fingerprint=E.es_fingerprint) as enst_equivs
FROM tx_def_summary_v N 
JOIN tx_def_summary_v E on N.cds_md5=E.cds_md5
WHERE N.tx_ac ~ '^NM_'
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
select TDS.hgnc,TDS.tx_ac,TASS.alt_ac,TASS.alt_strand,
	   aln_status(TDS.se_i,TASS.se_i,TASS.cigars) = 'NLxdi' as splign_refagree,
	   aln_status(TDS.se_i,TASB.se_i,TASB.cigars) = 'NLxdi' as blat_refagree,
	   aln_status(TDS.se_i,TASS.se_i,TASS.cigars) as splign_status,
	   aln_status(TDS.se_i,TASB.se_i,TASB.cigars) as blat_status,
	   aln_status(TDS.se_i,TASS.se_i,TASS.cigars) = aln_status(TDS.se_i,TASB.se_i,TASB.cigars) as splign_eq_blat,
	   NEE.enst_equivs,
	   cigar_stats(TASS.cigars) as splign_cigar_stats,
	   cigar_stats(TASB.cigars) as blat_cigar_stats,
	   TASS.cigars as splign_cigars,
	   TASB.cigars as blat_cigars
from tx_def_summary_v TDS
join tx_aln_summary_mv TASS on TDS.tx_ac=TASS.tx_ac and TASS.alt_aln_method='splign'
join tx_aln_summary_mv TASB on TASS.tx_ac=TASB.tx_ac and TASS.alt_ac=TASB.alt_ac and TASB.alt_aln_method='blat'
join nm_enst_equivalence_v NEE on TDS.tx_ac=NEE.tx_ac
join splign_blat_equivalence_v SBE on TASS.tx_ac=SBE.tx_ac and TASS.alt_ac=SBE.alt_ac
where TASS.alt_ac ~ '^NC_0000'
order by hgnc,tx_ac,alt_ac;
comment on view bermuda_v is 'the infamous bermuda doc!';


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


-- ucsc se diff stat
-- cigar => stats
-- refagree_match = NLxdi
-- 
