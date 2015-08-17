ChangeLog
^^^^^^^^^

0.2 series
==========

Issues targeted for 0.2 can be seen here:
https://bitbucket.org/biocommons/uta/issues?status=new&status=open&milestone=0.2


0.1 series
==========
	
0.1.7 (2014-05-10)
------------------

* use testing.postgresql package rather than existing db for tests
* `#157 <https://bitbucket.org/biocommons/hgvs/issue/157/>`_: commented out align2() method and updated remaining tests in uta.alignment.py
* `#157 <https://bitbucket.org/biocommons/hgvs/issue/157/>`_: fixed eutils and genomeutils doctests
* fixed sqlalchemy tests (finally)
* updated package metadata
* bermuda 2014-03 rc5
* bermuda 2014-03 rc4
* bermuda 2014-03 rc3
* u0 cigars should be semi-delimited
* merged bermuda1 branch
* `#147 <https://bitbucket.org/biocommons/hgvs/issue/147/>`_ - can generate test DB or full DB; replaced old version with this one.
* `#147 <https://bitbucket.org/biocommons/hgvs/issue/147/>`_ - incremental checkin; full psql to sqlite works; gcp tests in hgvs pass when using this DB.   Still need to create the test DB.
* added additional header info; added observations
* bermuda-table: fixed bug in human-readable indel coordinates
* bermuda-2014-03 rc 1
* lots of bermuda work incl. running (but broken) full table
* resurrected matchmaker code for ensembl lookup
* bermuda2 sql commit/rearrangement
* commit before rfur-bermuda merge
* added missing dependencies; pull test conf file from TEST_CONF if defined
* fixed alt_ac bug in tx_3way_v
* added eutils to setup.py
* sync with default
* modularized loading (during a reloading test)
* Makefile sync with sibling projects
* added trival indel at end discount; updated trival criteria
* fixed alt_ac in bic exonsets (missing underscore)
* close branch with misplaced commits, after grafting to default
* added stats str to cigar_stats return
* uppercase loaded and aligned sequences
* added misc/uta0-uta1-cigar-cmp
* set role for align_exons (missed because it bypasses the ORM)
* uppercase loaded and aligned sequences
* added misc/uta0-uta1-cigar-cmp
* set role for align_exons (missed because it bypasses the ORM)
* added cigar_stats_is_trivial
* added bermuda1 changes
* added indices; grant-permissions changes
* bermuda: materialize WITH NO DATA
* loading.py: grant permissions to PUBLIC, not uta_public (duh)
* added session authorization to loading.py (and etc/global.conf)
* allow multiple conf files
* updated grant-permissions cli subcommand; removed obsolete sql/grant-public-permissions.sql
* bic data updates to fix headers and cds_start_i; minor loading code updates to handle bic
* `#28 <https://bitbucket.org/biocommons/hgvs/issue/28/>`_ - fix headers; modify script to use exonset/txinfo writers to ensure consistency.
* in-place bic data updates (Rudy will handle scripts); minor loading code updates to handle bic
* restructured materialized views; added refresh script
* `#37 <https://bitbucket.org/biocommons/hgvs/issue/37/>`_ - exonset, txinfo files, & fasta files for BIC txs.
* `#28 <https://bitbucket.org/biocommons/hgvs/issue/28/>`_ - minor fix to script; METHOD=LRG in exonset file.
* `#28 <https://bitbucket.org/biocommons/hgvs/issue/28/>`_ - removed LRG_347 and LRG_163 fasta files (NR transcripts) from the bundle; not in the txtinfo and exonset files anyway.
* added sql/grant-public-permissions.sql
* store acmg uncompressed (easier \copy loading)
* added load-sequences to cli
* updated doc link on README
* auto merge
* `#120 <https://bitbucket.org/biocommons/hgvs/issue/120/>`_ - quick and dirty script to compare uta0/uta1 cigars
* `#28 <https://bitbucket.org/biocommons/hgvs/issue/28/>`_ - added fastas; includes 2 fastas (347 & 163) for public transcripts whose data is missing from the LRG TXT export, & thus from the tx info & exonset files.
* `#28 <https://bitbucket.org/biocommons/hgvs/issue/28/>`_ - fixed a duplication in the exonset file that comes about when a TX in the TXT export have 2 diff LRG proteins associated (only occurred for LRG_321).
* `#28 <https://bitbucket.org/biocommons/hgvs/issue/28/>`_ - updated inputs based on LRG fix for genomic exon coords on indels for transcripts on negative strands relative to GRChr37.   lrg.exonset.gz - METHOD=LRG_download (set in the script).
* updated bermuda-related sql
* updated bermuda views
* removed stale scripts in sbin/
* added bermuda_v and lots of other views, mat views, and functions
* pull fasta directory from conf; add --sql option hack; update loading/README
* `#28 <https://bitbucket.org/biocommons/hgvs/issue/28/>`_ - script to fetch exon/txinfo; corresponding outputs.   These look OK per the inputs from LRG, but the genomic coords for exons with indels relative to GRChr37 don't match... there may be an error in the LRG outputs.   Needs review prior to DB import.
* forgot to commit grant changes
* added grant-permissions to cli; added SERPINE1 gene and NC_ seqinfo filtering to test data
* update ensembl origin name and ncbi exonset suffix (missed in previous commit)
* seqinfo-filter: allow regexp based filtering (for NCs primarily)
* uta0-fetch: write fasta file
* add cds_md5 to transcript model and compute on loading
* added loading/README; cleaned up minor filename and scirpt inconsistencies
* provide additional feedback during loading txinfo and exonset files
* moved uta/db/loading.py to uta/loading.py; removed redundant schema declaration with tables
* skip existing txinfo where the transcript already exists
* added format filters and used to create more comprehensive loading test sets; added seq+seq_anno updating
* restructured loading/ for test and main
* updated loading diagram and added PDF (doc/misc-figures.pdf)
* added n_exons to exon_set_exons_v and transcript_exons_v
* fixed bug in ucsc-fetch-exonsets
* ensembl-fetch: skip redundant transcripts; write as .tmp files, then rename
* adding loading/test-data/ncbi.seqinfo.gz (missed from previous commit)
* re-added Seq & SeqAnno to schema; updated testdb loader
* added doc/misc-figures.odg
* updated ensembl-fetch to write sequences and catch errors (like undefined transcripts)
* first draft of ensembl-fetch
* merged and modified Rudy's uta0 extraction code
* Generate uta0 tx & exonset files
* updated test-data with larger set of genes and transcripts
* added testdb setup ("make -C loading testdb")
* moved sql to top level
* removed fetch-align-tasks
* finished switch to Kevin's aligner (and other minor changes)
* removed web
* implemented alignment with locus_lib_bio; dropped older alignment scripts
* added time remaining (based on average speed) to align stats
* added exon alignment -- cooking with gas now!
* loads full data sets from ncbi and ucsc!
* loads genes, txinfo, exonsets for first 100 genes alphabetically
* auto merge
* `#40 <https://bitbucket.org/biocommons/hgvs/issue/40/>`_ - updated script to allow optional creation of a test DB
* schema overhaul, again: no seq support, inlined accessions (no-dedup); updated gene loading (others pending)
* added ucsc-fetch-exonsets
* allow genes from stdin
* updated ncbi-fetch for genes, genomic exon sets, and transcript info
* finished (?) ncbi-fetch-exonsets
* added seqinfo and exonset tools
* use transcript hash as PK
* moved bin/* to sbin/ for consolidation
* added colorized logging
* merged grand-reorg branch
* last schema update for reorg
* improved consistency of align/alignment/aln/alt (in favor of alt) and transcript/tx
* schema refactor, again
* updated tests; uta.models still failing -- will fix after model updates
* dropped engine from cli call signatures (it was redundant)
* added uta.connect() function
* removed old test data
* eliminated lib/ to structure more a like typical python package
* full eutils loading worked
* huge loader improvements; more testing needed
* implemented gene loading via eutils
* schema updates; improved schema creating handling for postgresql
* implemented gene loading
* updated sqlalchemy database for new schema (DDL check okay!)
* `#61 <https://bitbucket.org/biocommons/hgvs/issue/61/>`_ - update test target to find tests and run coverage
* updated README with pypi info
* simple change to trigger dev branch build, maybe
* add link to drone.io test status; upload only bdist_egg and sdist (bdist causes install problems)
* Added tag 0.1.6 for changeset 8d6dd89831d9
* more doc and ci-test fixes

0.1.6 (2014-01-03)
------------------

* more doc and ci-test fixes
* Added tag 0.1.5 for changeset 4dbc0f653939
* fixed doc building and dropped upload_sphinx (in favor of upload_docs); moved docs to doc/source

0.1.5 (2014-01-03)
------------------

* fixed doc building and dropped upload_sphinx (in favor of upload_docs); moved docs to doc/source
* Removed tag 0.1.5
* Added tag 0.1.5 for changeset 6492c35b4f1d
* Added tag 0.1.3 for changeset 9f356eb03f8d
* misc doc updates, incl. version

0.1.3 (2014-01-03)
------------------

* misc doc updates, incl. version
* Added tag 0.1.2 for changeset 6b1edd242dc1
* Added tag 0.1.1 for changeset 6ef392a5eb58

0.1.2 (2013-12-30)
------------------

* Added tag 0.1.1 for changeset 6ef392a5eb58
* updated setup.py "license" attribute

0.1.1 (2013-12-30)
------------------

* updated setup.py "license" attribute
* s/locusdevelopment/invitae/
* removed license from ez_setup.py and sphinx_pypi_upload.py
* Added tag 0.1.0 for changeset 3d692ea0d5a2
* added Apache license and code boilerplate to all source files and scripts

0.1.0 (2013-12-30)
------------------

* `#58 <https://bitbucket.org/biocommons/hgvs/issue/58/>`_: migrated uta to publicly-accessible RDS instance and updated uta defaults
* `#62 <https://bitbucket.org/biocommons/hgvs/issue/62/>`_: synchronized setup files among UTA program components
* Added tag 0.0.3 for changeset 71ea26442ebe
* Created a web directory and moved the webservice in there for future expansion. Created a help page and additional API call for NM to genomic coords. Restructured the API links and versioned the URLs
* Makefile: new rule ve-test to execute tests in a fresh ve (as in with jenkins)
* added Apache license and code boilerplate to all source files and scripts
* added NEFL-dbSNP to the tests
* added get_tx_seq() method
* added jenkins target to makefile
* added sbin/fasta-hash-to-tsv
* bring back ez_setup
* changed NC_000014.10 to NC_000014.8
* corrected NC number for ch14 in genomeutils
* doc/ updates (incomplete)
* fetch-tx-* scripts: include gene name in response
* first offset commit
* fixed ci_to_human with additonal logic checks
* fixed start <= end for negative coordinates
* fixed strand bug in webservice api hgvs to genomic coords
* fixed uta.__version__, I think
* format edits
* removed localhost UTA_DB_URL setting in Makefile
* removed mapping code that now lives in hgvs
* start feature branch
* tests and bug fixes for offsets and strands
* transcriptmapper with offsets
* update default host to uta.invitae.com CNAME
* updated README.rst
* updated README; added sbin/uta-shell
* updated sbin/uta-pg-to-sqlite to include protein_hash and meta tables
* updated uta-pg-to-sqlite script to embed version number and name file (name no longer accepted from commandline)
* updated webservice index.html help
* updating intron mapping coordinates
* use uta0 database by default (rather than reece's db)
* uta-pg-to-sqlite: order records and output loading info

0.0.3 (2013-10-21)
------------------

* fixed uta.__version__, I think
* minor setup.py and Makefile changes; +x on bin/uta-webservice
* fixed and commented out DNAH11 tests; see TODO
* changed logic for db connection info (set UTA_DB_URL=postgresql://localhost/)
* don't run test_uta_db_sa_models.py (not ready yet)
* added sbin/dbsnp-rs-summary-to-tsv
* catch errors related to webservice calls
* added uta-webservice and requirements
* added tests for HGVSMapper.hgvsg_to_hgvsc
* updated Makefile and setup.py
* Added tag 0.0.2 for changeset a508efd70568
* implemented HGVSMapper.hgvsg_to_hgvsc with tests

0.0.2 (2013-10-15)
------------------

* implemented HGVSMapper.hgvsg_to_hgvsc with tests
* update hgvsmapper and add DNAH11 tests
* comment out doctests that require db connection
* raise InvalidIntervalError for intervals outside transcript bounds
* updated README with installation instructions
* removed stray import IPython
* changed max_extent default to False; updated TranscriptMapper and tests to use max_extent
* rewrote intervalmapper for min/max extent support, with tests
* Added tag 0.0.1 for changeset 43571336cc9e
* don't use ez_setup due to setuptools conflicts with other locus projects

0.0.1 (2013-10-09)
------------------

* don't use ez_setup due to setuptools conflicts with other locus projects
* update README with HGVSMapper instructions
* specifying hgvs-0.0.2 in dependency_links
* testing specifying hgvs-pre in dependency_links
* updated setup.py
* fixed make test
* incorporated HGVSMapper
* fixed pkg_dir for sdist
* reverted assertion
* removed bundled distribute_setup.py
* removed hgvs dependency; added ez_setup
* assertion for start==end==0; doc updates
* added cds<->ci conversion
* added example to README and updated misc/garcia-setup.py
* mostly passes John Garcia's tests
* minor commenting and addition of _debug_info in TranscriptMapper
* minor doc updates; fixed make test bug
* added support for sphinx_upload
* fix package_dir settting
* Added tag 0.0.0 for changeset 71d496797ab3
* hgid: use semver if avail, else hg id[:7]; add documentation to setup.py
