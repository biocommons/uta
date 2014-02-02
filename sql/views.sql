create or replace view gene_aliases_v as
select hgnc,unnest(array_append(string_to_array(aliases,','),hgnc)) as alias from gene ;


create or replace view exon_set_exons_v as
select ES.exon_set_id,
  array_to_string(array_agg(format('[%s,%s)',E.start_i,E.end_i) order by E.ord),',') as se_i,
  array_to_string(array_agg(E.start_i                           order by E.ord),',') as starts_i,
  array_to_string(array_agg(E.end_i                             order by E.ord),',') as ends_i,
  array_to_string(array_agg((E.end_i-E.start_i)                 order by E.ord),',') as lengths
from exon_set ES
join exon E on ES.exon_set_id=E.exon_set_id
group by ES.exon_set_id  ;


-- TODO: add alignment stats per exon
--drop view transcript_exon_sets_v cascade;
create or replace view transcript_exon_sets_v as
select T.hgnc,ES.tx_ac,ES.alt_ac,ES.alt_strand,ES.alt_aln_method,EXE.se_i,EXE.lengths
from exon_set ES
join transcript T on ES.tx_ac=T.ac
join exon_set_exons_v EXE on ES.exon_set_id=EXE.exon_set_id
;
-- where ES.alt_aln_method!='transcript';


--drop view tx_alt_exon_pairs_v;
create or replace view tx_alt_exon_pairs_v as
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


CREATE OR REPLACE VIEW split_blat_se_i_v AS
SELECT TES1.hgnc,TES1.tx_ac,TES1.alt_ac,TES1.alt_strand,TES1.se_i=TES2.se_i as match,
	   TES1.se_i as splign_se_i,TES2.se_i as blat_se_i
FROM transcript_exon_sets_v TES1
JOIN transcript_exon_sets_v TES2 ON TES1.tx_ac=TES2.tx_ac AND TES1.alt_ac=TES2.alt_ac
WHERE TES1.alt_aln_method='splign' AND TES2.alt_aln_method='blat';
