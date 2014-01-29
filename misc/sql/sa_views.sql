create or replace view gene_aliases_v as
select hgnc,unnest(array_append(string_to_array(aliases,','),hgnc)) as alias from gene ;


create or replace view exon_set_exons_v as
select ES.exon_set_id,
  array_to_string(array_agg(format('[%s,%s)',E.start_i,E.end_i) order by ES.alt_strand*E.start_i),',') as se_i,
  array_to_string(array_agg(E.start_i                           order by ES.alt_strand*E.start_i),',') as starts_i,
  array_to_string(array_agg(E.end_i                             order by ES.alt_strand*E.start_i),',') as ends_i,
  array_to_string(array_agg((E.end_i-E.start_i)                 order by ES.alt_strand*E.start_i),',') as lengths
from exon_set ES
join exon E on ES.exon_set_id=E.exon_set_id
group by ES.exon_set_id  ;


-- TODO: add alignment stats per exon
create or replace view transcript_exon_sets as
select T.hgnc,ES.alt_ac,ES.alt_strand,ES.alt_aln_method,EXE.se_i,EXE.lengths
from exon_set ES
join transcript T on ES.tx_ac=T.ac
join exon_set_exons_v EXE on ES.exon_set_id=EXE.exon_set_id
where ES.alt_aln_method!='transcript';


drop view _tx_alt_exon_pairs_v;
create or replace view _tx_alt_exon_pairs_v as
select TES.exon_set_id as tes_exon_set_id,AES.exon_set_id as aes_exon_set_id,
TES.tx_ac as tx_ac,AES.alt_ac as alt_ac,AES.alt_strand,AES.alt_aln_method,
TEX.ord as ord,TEX.exon_id as tx_exon_id,AEX.exon_id as alt_exon_id,
TEX.start_i as tx_start_i,TEX.end_i as tx_end_i, AEX.start_i as alt_start_i,AEX.end_i as alt_end_i
from exon_set TES
join exon_set AES on TES.tx_ac=AES.tx_ac and TES.alt_aln_method='transcript' and AES.alt_aln_method!='transcript'
join exon TEX on TES.exon_set_id=TEX.exon_set_id
join exon AEX on AES.exon_set_id=AEX.exon_set_id and TEX.ord=AEX.ord;

