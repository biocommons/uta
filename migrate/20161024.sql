begin;
update seq set seq=NULL where seq is not NULL;
commit;
vacuum analyze seq;

begin;
alter table exon_aln alter column tx_aseq drop not null;
alter table exon_aln alter column alt_aseq drop not null;
update exon_aln set tx_aseq=NULL, alt_aseq=NULL where tx_aseq is NULL or alt_aseq is NULL;
commit;
vacuum analyze exon_aln;
