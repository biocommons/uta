create or replace view uta1.gene_aliases_v as
select hgnc,unnest(array_append(string_to_array(aliases,','),hgnc)) as alias from gene ;


CREATE OR REPLACE VIEW tx_exon_aln_v AS 
SELECT T.hgnc,T.ac as tx_ac,AES.alt_ac,AES.alt_aln_method,AES.alt_strand,
	   TE.ord, TE.start_i as tx_start_i,TE.end_i as tx_end_i,
	   AE.start_i as alt_start_i, AE.end_i as alt_end_i,
	   EA.cigar, EA.tx_aseq, EA.alt_aseq,
	   TES.exon_set_id AS tx_exon_set_id,AES.exon_set_id as alt_exon_set_id,
	   TE.exon_id as tx_exon_id, AE.exon_id as alt_exon_id,
	   EA.exon_aln_id
FROM transcript T
JOIN exon_set TES ON T.ac=TES.tx_ac AND TES.alt_aln_method ='transcript'
JOIN exon_set AES on T.ac=AES.tx_ac and AES.alt_aln_method!='transcript'
JOIN exon TE ON TES.exon_set_id=TE.exon_set_id
JOIN exon AE ON AES.exon_set_id=AE.exon_set_id AND TE.ord=AE.ord
LEFT JOIN exon_aln EA ON TE.exon_id=EA.tx_exon_id AND AE.exon_id=EA.alt_exon_id;


create or replace view tx_alt_exon_pairs_v as
select T.hgnc,TES.exon_set_id as tes_exon_set_id,AES.exon_set_id as aes_exon_set_id,
TES.tx_ac as tx_ac,AES.alt_ac as alt_ac,AES.alt_strand,AES.alt_aln_method,
TEX.ord as ord,TEX.exon_id as tx_exon_id,AEX.exon_id as alt_exon_id,
TEX.start_i as tx_start_i,TEX.end_i as tx_end_i, AEX.start_i as alt_start_i,AEX.end_i as alt_end_i,
EA.exon_aln_id,EA.cigar
from exon_set TES
join transcript T on TES.tx_ac=T.ac
join exon_set AES on TES.tx_ac=AES.tx_ac and TES.alt_aln_method='transcript' and AES.alt_aln_method!='transcript'
join exon TEX on TES.exon_set_id=TEX.exon_set_id
join exon AEX on AES.exon_set_id=AEX.exon_set_id and TEX.ord=AEX.ord
left join exon_aln EA on EA.tx_exon_id=TEX.exon_id and EA.alt_exon_id=AEX.exon_id;


create or replace view exon_set_exons_v as
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
comment on view exon_set_exons_v is 'defining view of "flat" (aggregated) exons on a sequence; use _mv; for faster materialized version';


create or replace view  exon_set_exons_fp_v as
select ESE.*,md5(format('%s;%s',lower(ASA.seq_id),ESE.se_i)) as es_fingerprint
from exon_set_exons_v ESE
join seq_anno ASA on ESE.alt_ac=ASA.ac;
comment on view exon_set_exons_fp_v is 'flattened (aggregated) exons with exon set fingerprint';

create materialized view exon_set_exons_fp_mv as select * from exon_set_exons_fp_v WITH NO DATA;
create index exon_set_exons_fp_mv_tx_ac_ix on exon_set_exons_fp_mv(tx_ac);
create index exon_set_exons_fp_mv_alt_ac_ix on exon_set_exons_fp_mv(alt_ac);
create index exon_set_exons_fp_mv_alt_aln_method_ix on exon_set_exons_fp_mv(alt_aln_method);
grant select on exon_set_exons_fp_mv to public;


create or replace view tx_aln_cigar_dv as
select AES.tx_ac,AES.alt_ac,AES.alt_strand,AES.alt_aln_method,
	   count(*) as n_exons, string_agg(EA.cigar,','  order by TEX.ord) as cigars
from exon_set TES
join exon_set AES on TES.tx_ac=AES.tx_ac and TES.alt_aln_method='transcript' and AES.alt_aln_method!='transcript'
join exon TEX on TES.exon_set_id=TEX.exon_set_id
join exon AEX on AES.exon_set_id=AEX.exon_set_id and TEX.ord=AEX.ord
join exon_aln EA on EA.tx_exon_id=TEX.exon_id and EA.alt_exon_id=AEX.exon_id
group by AES.tx_ac,AES.alt_ac,AES.alt_strand,AES.alt_aln_method;

create materialized view tx_aln_cigar_mv as select * from tx_aln_cigar_dv WITH NO DATA;
create index tx_aln_cigar_mv_alt_ac_ix on tx_aln_cigar_mv(alt_ac);
create index tx_aln_cigar_mv_tx_ac_ix on tx_aln_cigar_mv(tx_ac);
create index tx_aln_cigar_mv_alt_aln_method_ix on tx_aln_cigar_mv(alt_aln_method);
analyze tx_aln_cigar_mv;
grant select on tx_aln_cigar_mv to public;


create or replace view tx_exon_set_summary_dv as
select hgnc,cds_md5,es_fingerprint,tx_ac,alt_ac,alt_aln_method,alt_strand,exon_set_id,n_exons,se_i,starts_i,ends_i,lengths
from transcript T
join exon_set_exons_fp_mv ESE on T.ac=ESE.tx_ac;

create materialized view tx_exon_set_summary_mv as select * from tx_exon_set_summary_dv WITH NO DATA;
create index tx_exon_set_summary_mv_cds_md5_ix on tx_exon_set_summary_mv(cds_md5);
create index tx_exon_set_summary_mv_es_fingerprint_ix on tx_exon_set_summary_mv(es_fingerprint);
create index tx_exon_set_summary_mv_tx_ac_ix on tx_exon_set_summary_mv(tx_ac);
create index tx_exon_set_summary_mv_alt_ac_ix on tx_exon_set_summary_mv(alt_ac);
create index tx_exon_set_summary_mv_alt_aln_method_ix on tx_exon_set_summary_mv(alt_aln_method);
analyze tx_exon_set_summary_mv;
grant select on tx_exon_set_summary_mv to public;

-- ideally, we'd include cds start and end here, but we don't yet map CDS
-- start and end to alt exon.  This are simple offsets in most cases,
-- except when there are indels, which is why I'm not doing that now.
create or replace view tx_def_summary_v as
select TESS.*,cds_start_i,cds_end_i
from tx_exon_set_summary_mv TESS
join transcript T on TESS.tx_ac=T.ac
where TESS.alt_aln_method = 'transcript';
comment on view tx_def_summary_v is 'transcript definitions, with exon structures';


create or replace view tx_aln_summary_v as
select TESS.*,TAC.cigars
from tx_exon_set_summary_mv as TESS
join tx_aln_cigar_mv TAC on TESS.tx_ac=TAC.tx_ac and TESS.alt_ac=TAC.alt_ac and TESS.alt_aln_method=TAC.alt_aln_method
where TESS.alt_aln_method != 'transcript';
comment on view tx_def_summary_v is 'transcript alignments on alternate seqeuences, with exon structures';

create materialized view tx_aln_summary_mv as select * from tx_aln_summary_v WITH NO DATA;
create index tx_aln_summary_mv_tx_ac_ix on tx_aln_summary_mv(tx_ac);
create index tx_aln_summary_mv_alt_ac_ix on tx_aln_summary_mv(alt_ac);
create index tx_aln_summary_mv_alt_aln_method_ix on tx_aln_summary_mv(alt_aln_method);
grant select on tx_aln_summary_mv to public;


