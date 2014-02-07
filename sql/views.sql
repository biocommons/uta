create or replace view gene_aliases_v as
select hgnc,unnest(array_append(string_to_array(aliases,','),hgnc)) as alias from gene ;


-- -- TODO: add alignment stats per exon
-- --drop view transcript_exon_sets_v cascade;
-- create or replace view transcript_exon_sets_v as
-- select T.hgnc,ES.tx_ac,ES.alt_ac,ES.alt_strand,ES.alt_aln_method,EXE.n_exons,EXE.se_i,EXE.lengths
-- from exon_set ES
-- join transcript T on ES.tx_ac=T.ac
-- join exon_set_exons_mv EXE on ES.exon_set_id=EXE.exon_set_id
-- ;


--drop view tx_alt_exon_pairs_v;
create or replace view tx_alt_exon_pairs_v as
select T.hgnc,TES.exon_set_id as tes_exon_set_id,AES.exon_set_id as aes_exon_set_id,
TES.tx_ac as tx_ac,AES.alt_ac as alt_ac,AES.alt_strand,AES.alt_aln_method,
TEX.ord as ord,TEX.exon_id as tx_exon_id,AEX.exon_id as alt_exon_id,
TEX.start_i as tx_start_i,TEX.end_i as tx_end_i, AEX.start_i as alt_start_i,AEX.end_i as alt_end_i,
EA.cigar
from exon_set TES
join transcript T on TES.tx_ac=T.ac
join exon_set AES on TES.tx_ac=AES.tx_ac and TES.alt_aln_method='transcript' and AES.alt_aln_method!='transcript'
join exon TEX on TES.exon_set_id=TEX.exon_set_id
join exon AEX on AES.exon_set_id=AEX.exon_set_id and TEX.ord=AEX.ord
left join exon_aln EA on EA.tx_exon_id=TEX.exon_id and EA.alt_exon_id=AEX.exon_id;

