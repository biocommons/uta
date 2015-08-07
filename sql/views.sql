-- USED BY: uta loading
CREATE OR REPLACE VIEW tx_alt_exon_pairs_v AS
SELECT T.hgnc,TES.exon_SET_id AS tes_exon_SET_id,AES.exon_SET_id AS aes_exon_SET_id,
       TES.tx_ac AS tx_ac,AES.alt_ac AS alt_ac,AES.alt_strand,AES.alt_aln_method,
       TEX.ORD AS ORD,TEX.exon_id AS tx_exon_id,AEX.exon_id AS alt_exon_id,
       TEX.start_i AS tx_start_i,TEX.END_i AS tx_END_i, AEX.start_i AS alt_start_i,AEX.END_i AS alt_END_i,
       EA.exon_aln_id,EA.cigar
FROM exon_SET tes
JOIN transcript t ON tes.tx_ac=t.ac
JOIN exon_SET aes ON tes.tx_ac=aes.tx_ac AND tes.alt_aln_method='transcript' AND aes.alt_aln_method!='transcript'
JOIN exon tex ON tes.exon_SET_id=tex.exon_SET_id
JOIN exon aex ON aes.exon_SET_id=aex.exon_SET_id AND tex.ORD=aex.ORD
LEFT JOIN exon_aln ea ON ea.tx_exon_id=tex.exon_id AND ea.alt_exon_id=AEX.exon_id;


----------------------------------------------------------------------------
-- USED BY: hgvs :-(
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
join _seq_anno_most_recent ASA on ESE.alt_ac=ASA.ac;
comment on view exon_set_exons_fp_v is 'flattened (aggregated) exons with exon set fingerprint';

create materialized view exon_set_exons_fp_mv as select * from exon_set_exons_fp_v WITH NO DATA;
create index exon_set_exons_fp_mv_tx_ac_ix on exon_set_exons_fp_mv(tx_ac);
create index exon_set_exons_fp_mv_alt_ac_ix on exon_set_exons_fp_mv(alt_ac);
create index exon_set_exons_fp_mv_alt_aln_method_ix on exon_set_exons_fp_mv(alt_aln_method);
grant select on exon_set_exons_fp_mv to public;

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

create or replace view tx_def_summary_dv as
select TESS.exon_set_id, TESS.tx_ac, TESS.alt_ac, TESS.alt_aln_method, TESS.alt_strand,
       TESS.hgnc, TESS.cds_md5, TESS.es_fingerprint, CEF.cds_es_fp, CEF.cds_exon_lengths_fp, 
       TESS.n_exons, TESS.se_i, CEF.cds_se_i, TESS.starts_i, TESS.ends_i, TESS.lengths, 
       T.cds_start_i, T.cds_end_i, CEF.cds_start_exon, CEF.cds_end_exon
from tx_exon_set_summary_mv TESS
join transcript T on TESS.tx_ac=T.ac
LEFT JOIN _cds_exons_fp_v CEF ON TESS.exon_set_id=CEF.exon_set_id
WHERE TESS.alt_aln_method = 'transcript';
comment on view tx_def_summary_dv is 'transcript definitions, with exon structures';

create materialized view tx_def_summary_mv as select * from tx_def_summary_dv WITH NO DATA;
comment on materialized view tx_def_summary_mv is 'transcript definitions, with exon structures and fingerprints';

create index tx_def_summary_mv_tx_ac on tx_def_summary_mv (tx_ac);
create index tx_def_summary_mv_alt_ac on tx_def_summary_mv (alt_ac);
create index tx_def_summary_mv_alt_aln_method on tx_def_summary_mv (alt_aln_method);
create index tx_def_summary_mv_hgnc on tx_def_summary_mv (hgnc);


-- backward compatbility for older view
create or replace view tx_def_summary_v as
select * from tx_def_summary_mv;


CREATE OR REPLACE VIEW tx_similarity_v AS
SELECT DISTINCT
       D1.tx_ac as tx_ac1, D2.tx_ac as tx_ac2,
       D1.hgnc = D2.hgnc as hgnc_eq,
       D1.cds_md5=D2.cds_md5 as cds_eq,
       D1.es_fingerprint=D2.es_fingerprint as es_fp_eq,
       D1.cds_es_fp=D2.cds_es_fp as cds_es_fp_eq,
       D1.cds_exon_lengths_fp=D2.cds_exon_lengths_fp as cds_exon_lengths_fp_eq
FROM tx_def_summary_mv D1
JOIN tx_def_summary_mv D2 on (D1.tx_ac != D2.tx_ac
                              and (D1.hgnc=D2.hgnc
                                   or D1.cds_md5=D2.cds_md5
                                   or D1.es_fingerprint=D2.es_fingerprint
                                   or D1.cds_es_fp=D2.cds_es_fp
                                   or D1.cds_exon_lengths_fp=D2.cds_exon_lengths_fp
                                   ));
