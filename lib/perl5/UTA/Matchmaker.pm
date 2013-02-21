package UTA::Matchmaker;

use strict;
use warnings;

use BerkeleyDB;
use Digest::MD5 qw(md5_hex);
use Log::Log4perl;
use MLDBM qw(BerkeleyDB::Btree FreezeThaw);

use Bio::EnsEMBL::Registry;
use Bio::EnsEMBL::ApiVersion;

use UTA::GeneTranscriptInfo;


sub new {
  my $class = shift;
  my $self = bless({@_}, $class);

  $self->{'logger'} = Log::Log4perl->get_logger();

  if (exists $self->{'cache-filename'}) {
	tie( %{$self->{'cache'}},
		 'MLDBM',
		 -Filename => $self->{'cache-filename'},
		 -Flags => DB_CREATE
		)
	  or die(sprintf("Couldn't open db %s: $!", $self->{'cache-filename'}));

	$self->{logger}->info(
	  sprintf('using cache (%s); %d existing keys',
			  $self->{'cache-filename'},
			  scalar keys %{$self->{cache}}));
  }

  return $self;
}

sub connect($) {
  my $self = shift;
  return if exists $self->{'registry'};

  $self->{'registry'} = 'Bio::EnsEMBL::Registry';
  $self->{'registry'}->load_registry_from_db(
    -host => $self->{'host'},
	-port => $self->{'port'},
    -user => $self->{'user'},
   );
  $self->{logger}->info(sprintf("connected to %s%s@%s:%s, version %s\n",
								$self->{'user'},
								defined $self->{'pass'} ? $self->{'pass'} : '',
								$self->{'host'}, $self->{'port'},
								software_version()));

  foreach my $aspec (
	[ 'cga'  , 'Human' , 'Core'           , 'Gene'        ],
	[ 'csa'  , 'Human' , 'Core'           , 'Slice'       ],
	[ 'cta'  , 'Human' , 'Core'           , 'Transcript'  ],
	[ 'ofga' , 'Human' , 'OtherFeatures'  , 'Gene'        ],
	[ 'ofsa' , 'Human' , 'OtherFeatures'  , 'Slice'       ],
	[ 'ofta' , 'Human' , 'OtherFeatures'  , 'Transcript'  ],
   ) {
    $self->add_adaptor(@$aspec);
  }
}

sub add_adaptor($%) {
  my ($self,$id,$sp,$db,$obj) = @_;
  my $a = $self->{'registry'}->get_adaptor( $sp, $db, $obj );
  defined $a || die("Couldn't get adaptor for ( $sp, $db, $obj ): failed");
  $self->{logger}->debug(sprintf('created <%s,%s,%s> adaptor (%s)',$sp,$db,$obj,$id));
  $self->{$id} = $a;
}


sub fetch_cached($$) {
  my ($self,$hgnc) = @_;
  if (defined $self->{cache}
		and exists $self->{cache}->{$hgnc}) {
	$self->{logger}->debug(sprintf('retrieved %s from cache',$hgnc));
	return $self->{cache}->{$hgnc};
  }
  return undef;
}

sub store_cached($$$) {
  my ($self,$hgnc,$gti) = @_;
  if (defined $self->{cache}) {
	$self->{cache}->{$hgnc} = $gti;
	$self->{logger}->debug(sprintf('cached %s',$hgnc));
  }
  return;
}


sub match_by_gene($$) {
  my $self = shift;
  my $hgnc = shift;

  my $gti = $self->fetch_cached($hgnc);
  return $gti if defined $gti;

  $self->connect();							# NOP if already connected

  # there may be multiple ENSGs per HGNC name (e.g., GALT)
  my @genes = @{ $self->{'cga'}->fetch_all_by_external_name($hgnc) };
  @genes = grep { $_->display_id() =~ m/^ENSG/ } @genes;

  # fetch union of ENSTs for genes
  my @ensg_ids = map { $_->display_id() } @genes;
  my @ensts = map { @{ $_->get_all_Transcripts() } } @genes;
  @ensts = grep { $_->display_id() =~ m/^ENST/ } @ensts;
  @ensts = values({ map { $_->display_id() => $_ } @ensts }); # uniquify by id

  # fetch union of NMs for genes
  my @nms = map { @{ $self->{'ofta'}->fetch_all_by_Slice( $_->feature_Slice() ) } } @genes;
  @nms = grep { $_->display_id() =~ m/^NM_/ } @nms;
  @nms = values({ map { $_->display_id() => $_ } @nms }); # uniquify by id

  my %nm_tis   = map { $_->display_id() => tx_info($_->transform('chromosome')) } @nms;
  my %enst_tis = map { $_->display_id() => tx_info($_                         ) } @ensts;
  my %cmps = map { $_ => [] } qw(CC CE Ce cC cE ce);
  for my $nm_id (keys %nm_tis) {
	for my $enst_id (keys %enst_tis) {
	  my $cmp = ti_cmp($nm_tis{$nm_id},$enst_tis{$enst_id});
	  push( @{$cmps{$cmp} }, [$nm_id,$enst_id] );
	}
  }

  $gti = UTA::GeneTranscriptInfo->new(
	'hgnc' => $hgnc,
	'ensg_ids' => \@ensg_ids,
	'enst_ids' => [map {$_->display_id()} @ensts],
	'nm_ids' => [map {$_->display_id()} @nms],
	'cmps' => \%cmps,
   );

  $self->store_cached($hgnc,$gti);			# NOP if cache NA
  return $gti;
}



############################################################################

sub ti_cmp {
  my ($ti1,$ti2) = @_;
  my $c = $ti1->{'cds-md5'}    eq $ti2->{'cds-md5'}   ? 'C' : 'c';
  my $e = $ti1->{'exons'}  	   eq $ti2->{'exons'}      ? 'E' :
	$ti1->{'cds-exons'}  	   eq $ti2->{'cds-exons'}  ? 'C' : 'e';
  return "$c$e";
}

sub tx_info {
  my $t = shift;
  my $cds_start = $t->coding_region_start();
  my $cds_end = $t->coding_region_end();
  my $cds_seq = $t->translateable_seq();
  my @exons_se = map {[$_->start(),$_->end()]} @{ $t->get_all_Exons() };
  my @cds_exons_se = map {[$_->start(),$_->end()]} @{ $t->get_all_translateable_Exons() };
  my $pseudo = $cds_seq eq '';				# cds empty => pseudogene
  # or do I want seq_region_name since we're should be at the chromosome level?
  my ($chr) = $t->slice()->name() =~ m/chromosome:GRCh37:([^:]+):/;
  my $g = $t->get_Gene();
  my $gene_name = $g->display_id();
  my @dblinks = @{$g->get_all_DBLinks()};   # perhaps empty
  my $ccds   = join(',',uniq(grep {/^CCDS/} map {$_->display_id()} @dblinks));
  my $refseq = join(',',uniq(grep {/^NM/}   map {$_->display_id()} @dblinks));
  return {
    'id' => $t->display_id(),
    'chr' => $chr,
    'gene' => $gene_name,
    'pseudo' => $pseudo,
    'ccds' => $ccds,
    'refseq' => $refseq,
    'strand' => $t->strand(),
    'cds-start' => $t->coding_region_start(),
    'cds-end' => $t->coding_region_end(),
    'cds-length' => length($cds_seq),
    'n-exons' => $#exons_se+1,
    'exons' => se_str(@exons_se),
    'cds-exons' => se_str(@cds_exons_se),
    'cds-md5' => md5_hex($cds_seq),
  };
}

sub uniq {
  return keys %{{ map {$_=>1} @_ }};
}

sub se_str {
  join(',', map {sprintf('[%s,%s]', $_->[0]||'?', $_->[1]||'?')} @_);
}


1;
