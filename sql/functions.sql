create or replace function seq_md5(in seq text, out seq_md5 text)
strict immutable as
$$select md5(upper(seq))$$
language sql;

comment on function seq_md5(in seq text, out seq_md5 text) is 'compute md5 of sequence (uppercased)';


create or replace function subseq(in seq text, in start_i int, in end_i int, out seq text)
strict immutable as
$$select substr(seq,start_i+1,end_i-start_i)$$
language sql;

comment on function subseq(in seq text, in start_i int, in end_i int, out seq text) is 'extract subseq; uses interbase coords!';

create or replace function extract_ncbi_accessions(s text) returns setof text language sql as $_$ select unnest(regexp_matches(s, '(N[CGMRTW]_\d+\.\d+)', 'g')) $_$;

create or replace function accession_base(s text) returns text strict immutable language sql as $_$ select split_part(s,'.',1) $_$;



-- -- http://stackoverflow.com/questions/12414750/
-- CREATE OR REPLACE FUNCTION zip(anyarray, anyarray)
--   RETURNS SETOF anyarray LANGUAGE SQL AS
-- $func$
-- SELECT ARRAY[a,b] FROM (SELECT unnest($1) AS a, unnest($2) AS b) x;
-- $func$;
-- 
-- CREATE OR REPLACE FUNCTION zip2(anyarray, anyarray)
--   RETURNS SETOF anyarray LANGUAGE SQL AS
-- $func$
-- SELECT array_agg_mult(ARRAY[ARRAY[a,b]])
-- FROM (SELECT unnest($1) AS a, unnest($2) AS b) x;
-- $func$;


