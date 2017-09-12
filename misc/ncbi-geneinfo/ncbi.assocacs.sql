create table assocacs (
       hgnc text,
       tx_ac text,
       gene_id integer,
       pro_ac text,
       origin text
       );

create index assocacs_hgnc on assocacs(hgnc);
create index assocacs_gene_id on assocacs(gene_id);
create index assocacs_tx_ac on assocacs(tx_ac);
create index assocacs_pro_ac on assocacs(pro_ac);
create unique index unique_pair_in_origin on assocacs(origin,tx_ac,pro_ac);

comment on table assocacs is 'transcript-protein accession pairs associated in source databases';



