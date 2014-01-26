create or replace view gene_aliases as select hgnc,unnest(array_append(string_to_array(aliases,','),hgnc)) as alias from gene ;
