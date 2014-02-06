create or replace function cigar_status(IN cigar text, OUT status text)
strict immutable language sql as
$$select concat(
         case when cigar ~ 'X' then 'X' else 'x' end,
         case when cigar ~ 'D' then 'D' else 'd' end,
         case when cigar ~ 'I' then 'I' else 'i' end
         )
$$;


create or replace function aln_status(IN tx_se_i text, IN alt_se_i text, IN cigars text, OUT status text)
strict immutable language plperl as
$$
	use strict;
	use warnings;

	# return NLxdi-string
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


create or replace function cigar_stats(
	   IN cigar text,
	   out stats text
	   --#OUT l1 int,
	   --OUT l2 int,
	   --OUT n int,
	   --OUT e int,
	   --OUT x int,
	   --OUT d int,
	   --OUT i int
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



