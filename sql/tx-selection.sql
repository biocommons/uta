-- queries to select representative genes and transcripts for testing
-- these are based of of the uta0 schema.

-- all of the following occurs in the uta0 schema

-- Since uta0 was tested extensively, we'll use transcript accessions
-- that are in uta0 and remain currently available (i.e., in uta1).
-- Generate the list of current transcripts by:
-- $ gzip -cd loading/data/ncbi.txinfo.gz | tail -n+2 | cut -f2 | sort -u >/tmp/uta1ac


-- load a list of current transcripts 
create temp table uta1ac (ac text);
\copy uta1ac from '/tmp/uta1ac'

-- I get:
-- (default-2.7)snafu$ gzip -cd loading/data/ncbi.txinfo.gz | tail -n+2 | cut -f2 | sort -u >|/tmp/uta1ac 
-- loading/data/ncbi.txinfo.gz:	 61.8%
-- (default-2.7)snafu$ wc -l /tmp/uta1ac
-- 34813 /tmp/uta1ac


-- create a view of 3-exon transcripts in common 
create or replace temp view avail as 
select status,strand,gene,ac from transcript_table_mv
natural join uta1ac
where n_t_exons=3;

-- a function to return a set of avail rows for a given status,strand
create or replace function s5(sta text,str integer)
returns setof avail as 
$$select * from avail where status=sta and strand=str limit 5$$
language sql;

-- then build a select statement from the union of those
select array_to_string(array_agg(distinct format($$select * from s5('%s',%s)$$,status,strand)),' UNION ') from avail;

-- copy paste that into psql
create temp view reps as
select * from s5('nlxdi',-1)
UNION select * from s5('NLXdi',-1) 
UNION select * from s5('NLXdi',1)
UNION select * from s5('NLxdi',-1)
UNION select * from s5('NLxdi',1) 
UNION select * from s5('NlXDi',-1)
UNION select * from s5('NlXdI',-1) 
UNION select * from s5('NlXdI',1) 
UNION select * from s5('NlxDi',-1)
UNION select * from s5('NlxDi',1) 
UNION select * from s5('NlxdI',-1) 
UNION select * from s5('NlxdI',1) 
UNION select * from s5('nlXDI',-1)
UNION select * from s5('nlxdI',1) 
UNION select * from s5('nlxdi',1)
;

-- write them to loading test files (the Makefile will take over from here)
\copy (select distinct gene from reps) to 'loading/test-data/genes'
\copy (select distinct ac from reps) to 'loading/test-data/acs'
