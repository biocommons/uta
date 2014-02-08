alter database uta_dev set search_path=uta1;

grant usage on schema uta1 to uta_public;

grant select on uta1.exon to uta_public;
grant select on uta1.exon_alignments_v to uta_public;
grant select on uta1.exon_aln to uta_public;
grant select on uta1.exon_set to uta_public;
grant select on uta1.exon_set_exons_fp_mv to uta_public;
grant select on uta1.exon_set_exons_fp_v to uta_public;
grant select on uta1.exon_set_exons_v to uta_public;
grant select on uta1.gene to uta_public;
grant select on uta1.meta to uta_public;
grant select on uta1.nm_enst_equivalence_v to uta_public;
grant select on uta1.origin to uta_public;
grant select on uta1.seq to uta_public;
grant select on uta1.seq_anno to uta_public;
grant select on uta1.splign_blat_equivalence_v to uta_public;
grant select on uta1.transcript to uta_public;
grant select on uta1.tx_aln_cigar_dv to uta_public;
grant select on uta1.tx_aln_cigar_mv to uta_public;
grant select on uta1.tx_aln_summary_mv to uta_public;
grant select on uta1.tx_aln_summary_v to uta_public;
grant select on uta1.tx_def_summary_v to uta_public;
grant select on uta1.tx_exon_set_summary_dv to uta_public;
grant select on uta1.tx_exon_set_summary_mv to uta_public;
