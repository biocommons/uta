CREATE OR REPLACE VIEW transcript_exons_cds_clipped_v AS
SELECT ES.exon_set_id,T.ac,E.ord,
	   greatest(E.start_i,T.cds_start_i) as start_i,
	   least(E.end_i,T.cds_end_i) as end_i
FROM transcript T
join exon_set ES on T.ac = ES.tx_ac
join exon E on ES.exon_set_id=E.exon_set_id
WHERE E.start_i <= T.cds_end_i AND E.end_i >= T.cds_start_i
;


-- -- TODO: add alignment stats per exon
-- --drop view transcript_exon_sets_v cascade;
-- create or replace view transcript_exon_sets_v as
-- select T.hgnc,ES.tx_ac,ES.alt_ac,ES.alt_strand,ES.alt_aln_method,EXE.n_exons,EXE.se_i,EXE.lengths
-- from exon_set ES
-- join transcript T on ES.tx_ac=T.ac
-- join exon_set_exons_mv EXE on ES.exon_set_id=EXE.exon_set_id
-- ;


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


