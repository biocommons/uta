#!/usr/bin/env perl

use strict;
use warnings;

use Data::Dumper;

sub cigar_cmp($$) {
	# given two cigar strings, perhaps comma-sep, return consensus at agreement, ^^^ elsewhere
	my ($c1,$c2) = @_;
	$c1 =~ s/,//g;
	$c2 =~ s/,//g;

	my @e1 = $c1 =~ m/\d+\D/g;
	my @e2 = $c2 =~ m/\d+\D/g;
	
	my $min = $#e1 < $#e2 ? $#e1 : $#e2;
	my @rv = map {$e1[$_] eq $e2[$_] ? ' ' x length($e1[$_]) : '^' x length($e1[$_])} 0..$min;

	if ($#e1 > $min) {
		push(@rv,'+e1',@e1[$min+1,$#e1]);
	} elsif ($#e2 > $min) {
		push(@rv,'+e2',@e2[$min+1,$#e2]);
	}
	
	return join(',',@rv);
}



# IN tx_se_i text, IN alt_se_i text, IN cigars text, OUT status text)
sub aln_status {
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
	print(">> $rv\n");
	return $rv;
};
	

sub cigar_stats($) {
	# return stats for cigar string, possibly comma-separated
	my ($cigars) = @_;
	my (%rv) = map {$_=>0} qw(= X D I);

	$cigars =~ s/,//g;
	my @elems = $cigars =~ m/\d+\D/g;
	
	$rv{n} = $#elems + 1;
	foreach my $e (@elems) {
		my ($n,$op) = $e =~ m/^(\d+)(\D)/;
		$rv{$op} += $n;
	}
	
	$rv{'l1'} = $rv{'='} + $rv{'X'} + $rv{'D'};
	$rv{'l2'} = $rv{'='} + $rv{'X'} + $rv{'I'};

	return %rv;
}




print(
	cigar_cmp(
		'141=,815=,21=1X210=,194=,167=,61=,200=,3113=1I1248=',
		'142=,815=,21=1X210=,194=,167=,61=,200=,3113=1I1248=',
	), "\n" );

print(
	aln_status( '122740342,122740483;122748592,122749407;122749612,122749844;122755302,122755496;122759911,122760078;122760832,122760893;122768492,122768692;122770099,122774461',
				'122740342,122740483;122748592,122749407;122749612,122749844;122755302,122755496;122759911,122760078;122760832,122760893;122768492,122768692;122770099,122774461',
				'141=,815=,21=1X210=,194=,167=,61=,200=,3113=1I1248=' ),
	"\n"
	);
	
print( Dumper( \{cigar_stats('141=,815=,21=1X210=,194=,167=,61=,200=,3113=1I1248=')} ), "\n" );
