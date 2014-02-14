create or replace function sv_cmp(IN sep text, IN cigar1 text, IN cigar2 text, OUT mask text)
strict immutable language plperl as
$$
    # given two sep-separated strings, a mask with ^^^ highlighting disagreement
    my ($sep,$c1,$c2) = @_;
    
    my @e1 = split($sep,$c1);
    my @e2 = split($sep,$c2);

    my $min = $#e1 < $#e2 ? $#e1 : $#e2;
    my @rv = map {$e1[$_] eq $e2[$_] ? ' ' x length($e1[$_]) : '^' x length($e1[$_])} 0..$min;

    if ($#e1 > $min) {
        push(@rv,'+e1',@e1[$min+1,$#e1]);
    } elsif ($#e2 > $min) {
        push(@rv,'+e2',@e2[$min+1,$#e2]);
    }
    
    return join($sep,@rv);
$$;


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


create or replace function cigar_stats_str(
       IN cigar text,
       out stats text
       )
strict immutable language plperl as
$$
    use strict;
    use warnings;

    my ($cigars) = @_;
    my (%rv) = map {$_=>0} qw(e x d i);

    $cigars =~ s/,//g;
    my @elems = $cigars =~ m/\d+\D/g;
    
    $rv{n} = $#elems + 1;
    foreach my $e (@elems) {
        my ($n,$op) = $e =~ m/(\d+)(\D)/;
        $op = $op eq '=' ? 'e' : lc($op);
        $rv{$op} += $n;
    }
    
    $rv{'l1'} = $rv{'e'} + $rv{'x'} + $rv{'d'};
    $rv{'l2'} = $rv{'e'} + $rv{'x'} + $rv{'i'};

    return "l1:$rv{l1}; l2:$rv{l2}; n:$rv{n}; =:$rv{e}; x:$rv{x}; d:$rv{d}; i:$rv{i}";
    return \%rv;
$$;


create or replace function cigar_stats(
       IN cigars text,
       OUT collapsed_cigar text,
       OUT l1 int,
       OUT l2 int,
       OUT n_ex int,
       OUT n_ops int,
       OUT n_e int,
       OUT n_x int,
       OUT n_d int,
       OUT n_i int,
       OUT t_e int,
       OUT t_x int,
       OUT t_d int,
       OUT t_i int,
	   OUT stats text
       )
strict immutable language plperl as
$$
    use strict;
    use warnings;

    my ($cigars) = @_;
    my (%rv) = map {$_=>0} qw(l1 l2 n_ex n_ops   
                              n_e n_x n_d n_i
                              t_e t_x t_d t_i);

    $rv{'n_ex'} = $cigars =~ tr/,/,/ + 1;

    my $cigar = $cigars;
    $cigar =~ s/,//g;
    while ($cigar =~ s/(\d+)(\D)(\d+)\2/sprintf("%d%s",$1+$3,$2)/eg) {};
    $rv{'collapsed_cigar'} = $cigar;

    my @elems = $cigar =~ m/\d+\D/g;
    $rv{'n_ops'} = $#elems + 1;

    foreach my $e (@elems) {
        my ($n,$op) = $e =~ m/(\d+)(\D)/;
        $op = $op eq '=' ? 'e' : lc($op);
        $rv{"n_$op"} += 1;
        $rv{"t_$op"} += $n;
    }
    
    $rv{'l1'} = $rv{'t_e'} + $rv{'t_x'} + $rv{'t_d'};
    $rv{'l2'} = $rv{'t_e'} + $rv{'t_x'} + $rv{'t_i'};
    $rv{'stats'} = join('; ', map {sprintf("%s:%s",$_,$rv{$_})} qw(l1 l2 n_ex n_ops n_e n_x n_d n_i t_e t_x t_d t_i));
    return \%rv;
$$;



CREATE OR REPLACE FUNCTION cigar_stats_is_trivial(RECORD)
RETURNS BOOLEAN LANGUAGE plperl STRICT IMMUTABLE AS 
$$
use strict;
use warnings;

my ($r) = @_;
return (
	   ($r->{n_ops} <= 4)
	   and ($r->{n_d} + $r->{n_i} <= 2)
	   )	   
	   ? 1 : 0;
$$;


