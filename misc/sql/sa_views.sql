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
