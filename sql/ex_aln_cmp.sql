create or replace view _exons_v as
select ES.exon_set_id,exon_id,alt_aln_method,alt_strand,alt_ac,tx_ac,ord,start_i,end_i
from exon_set ES
join exon E on ES.exon_set_id=E.exon_set_id;

drop view exon_aln_cmp_v;
create or replace view exon_aln_cmp_v as
select T.hgnc,exists(select * from acmg_mr where hgnc=T.hgnc) as mr,
	   ES.alt_ac,ES.alt_strand,ES.tx_ac,ES.ord,
	   ES.start_i as splign_start_i,ES.end_i as splign_end_i,
	   EB.start_i as blat_start_i,EB.end_i as blat_end_i,
	   (ES.start_i=EB.start_i and ES.end_i=EB.end_i and ES.alt_strand=EB.alt_strand) as match,
	   abs(ES.start_i-EB.start_i) as sdiff, abs(ES.end_i-EB.end_i) as ediff,
	   ES.exon_id as splign_exon_id,EB.exon_id as blat_exon_i
from (select ac from transcript UNION select tx_ac as ac from exon_set) as TX
left join transcript T on TX.ac=T.ac
left join _exons_v ES on T.ac=ES.tx_ac and ES.alt_aln_method='splign'
left join _exons_v EB on T.ac=EB.tx_ac and EB.alt_aln_method='blat' and ES.ord=EB.ord and ES.alt_ac=EB.alt_ac
where ES.alt_ac in (
'NC_000001.10', 'NC_000002.11', 'NC_000003.11', 'NC_000004.11', 'NC_000005.9', 'NC_000006.11',
'NC_000007.13', 'NC_000008.10', 'NC_000009.11', 'NC_000010.10', 'NC_000011.9', 'NC_000012.11',
'NC_000013.10', 'NC_000014.8', 'NC_000015.9', 'NC_000016.9', 'NC_000017.10', 'NC_000018.9',
'NC_000019.9', 'NC_000020.10', 'NC_000021.8', 'NC_000022.10', 'NC_000023.10', 'NC_000024.9'
)
order by tx_ac,ord;


CREATE OR REPLACE FUNCTION bin10s(n) RETURNS TEXT
LANGUAGE PLSQL STRICT IMMUTABLE AS $$
BEGIN
  IF n == 0 THEN
  	RETURN '=0'
  RETURN format("[%d,%d)",int(log(n)),int(log(n
