create or replace function aln_status(IN tx_se_i text, IN alt_se_i text, IN cigars text, OUT status text)
strict immutable language plperl as		 
$$
    # returns NLxdi-string

    use strict;
    use warnings;

    my ($tx_se_i,$alt_se_i,$cigars) = @_;
    my (@tx_se_i) = map( { [split(',',$_)] } split(';',$tx_se_i) );
    my (@tx_lens) = map( { $_->[1]-$_->[0] } @tx_se_i );

    my (@alt_se_i) = map( { [split(',',$_)] } split(';',$alt_se_i) );
    my (@alt_lens) = map( { $_->[1]-$_->[0] } @alt_se_i );

    my $N = $#tx_se_i == $#alt_se_i ? 'N' : 'n';
    my $L = join(',',@tx_lens) eq join(',',@alt_lens) ? 'L' : 'l';
    my $X = $cigars =~ 'X' ? 'X' : 'x';
    my $D = $cigars =~ 'D' ? 'D' : 'd';
    my $I = $cigars =~ 'I' ? 'I' : 'i';
    
    my $rv = "$N$L$X$D$I";
    return $rv;
$$;

create or replace function u0_to_u1_cigar(c text) returns text
strict immutable language plperl as
$$
my ($c) = @_;
$c =~ tr/DIM/di=/;
$c =~ tr/di/ID/;
return $c;
$$;

create or replace function u0_to_u1_status(s text) returns text
strict immutable language plperl as
$$
my ($_) = @_;
s/dI/Di/ or s/Di/dI/;
return $_;
$$;



create or replace view u0_t_exons_v as 
select ac,count(*) as t_n_exons,
	   array_to_string(array_agg(format('%s,%s',start_i,end_i) order by ord),';') as t_se_i,
	   array_to_string(array_agg(end_i-start_i order by ord),';') as t_lengths
from uta0.transcript_exon
group by ac;

create or replace view u0_g_exons_v as 
select GE.ac,G.strand,count(*) as g_n_exons,
	   array_to_string(array_agg(format('%s,%s',GE.start_i,GE.end_i) order by ord),';') as g_se_i,
	   array_to_string(array_agg(GE.end_i-GE.start_i order by ord),';') as g_lengths 
from uta0.genomic_exon GE
join uta0.transcript T on GE.ac=T.ac
join uta0.gene G on T.gene=G.gene
group by GE.ac,G.strand;

create or replace view u0_gt_summary_v as
select TES.ac,aln_status(t_se_i,g_se_i,u0_to_u1_cigar(TGA.cigars)) as status,GES.strand,t_n_exons,t_se_i,t_lengths,g_n_exons,g_se_i,g_lengths,u0_to_u1_cigar(TGA.cigars) as cigars
from u0_t_exons_v as TES
left join u0_g_exons_v GES on TES.ac=GES.ac
left join uta0.transcript_cigars_v TGA on TES.ac=TGA.ac;


create or replace view u1_t_exons_v as
select tx_ac as ac,n_exons as t_n_exons,se_i as t_se_i,array_to_string(lengths,';') as t_lengths
from uta1.tx_def_summary_v;

create or replace view u1_g_exons_v as 
select tx_ac as ac,alt_strand as strand,n_exons as g_n_exons,se_i as g_se_i,array_to_string(lengths,';') as g_lengths
from uta1.tx_aln_summary_v
where alt_ac~'^NC_0000' and alt_aln_method='splign';

create or replace view u1_gt_summary_v as
select TES.ac,aln_status(t_se_i,g_se_i,cigars) as status,GES.strand,t_n_exons,t_se_i,t_lengths,g_n_exons,g_se_i,g_lengths,TGA.cigars
from u1_t_exons_v as TES
left join u1_g_exons_v GES on TES.ac=GES.ac
left join uta1.tx_aln_cigar_mv TGA on TES.ac=TGA.tx_ac
where TGA.alt_ac~'^NC_0000' and TGA.alt_aln_method='splign';

create table ac_alts as
select tx_ac as ac,array_to_string(array_agg(alt_ac),',') as alts
from uta1.tx_aln_summary_mv
where alt_ac~'^NC_0000' and alt_aln_method='splign' group by tx_ac;


create or replace view u01_v as 
select T.gene, AA.alts, u0.ac, u0.strand,
	   u0.status as u0_status, u1.status as u1_status,

	   u0.t_n_exons as u0_t_n_exons, u1.t_n_exons as u1_t_n_exons,
	   u0.g_n_exons as u0_g_n_exons, u1.g_n_exons as u1_g_n_exons,

	   u0.t_lengths as u0_t_lengths, u1.t_lengths as u1_t_lengths,
	   u0.g_lengths as u0_g_lengths, u1.g_lengths as u1_g_lengths,

	   u0.t_se_i as u0_t_se_i, u1.t_se_i as u1_t_se_i, 
	   u0.g_se_i as u0_g_se_i, u1.g_se_i as u1_g_se_i,

	   u0.cigars as u0_cigars, u1.cigars as u1_cigars

from u0_gt_summary_v as u0
join u1_gt_summary_v u1 on u0.ac=u1.ac
left join ac_alts AA on u0.ac=AA.ac
left join uta0.transcript T on u0.ac=T.ac
;


create materialized view u01_mv as select * from u01_v;
