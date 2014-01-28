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


create or replace view seq_anno_ncbi_v as
select seq_id,array_to_string(array_agg(distinct ac order by ac),',') as aliases
from seq_anno
where ac ~ '^N[CGMRW]'
group by seq_id;


drop view transcript_alignments_v;
create or replace view transcript_alignments_v as
select ES.exon_set_id,G.hgnc,
	T.transcript_id,T.seq_id tx_seq_id,TSA.aliases as tx_aliases,
	ES.alt_seq_id,ASA.aliases as alt_aliases,
	T.cds_start_i,T.cds_end_i,EXE.se_i,EXE.lengths
from exon_set ES
join transcript T on ES.transcript_id=T.transcript_id
join gene G on T.gene_id=G.gene_id
join seq_anno_ncbi_v TSA on T.seq_id=TSA.seq_id
join seq_anno_ncbi_v ASA on ES.alt_seq_id=ASA.seq_id
join exon_set_exons_v EXE on ES.exon_set_id=EXE.exon_set_id;
