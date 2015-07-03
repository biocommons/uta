create table associated_accessions (
    associated_accession_id serial primary key,
    hgnc text,
    tx_ac text,
    pro_ac text,
    origin text not null,
    added timestamp with time zone not null default now()
    );

create index associated_accessions_hgnc on associated_accessions(hgnc);
create index associated_accessions_tx_ac on associated_accessions(tx_ac);
create index associated_accessions_pro_ac on associated_accessions(pro_ac);
create unique index unique_pair_in_origin on associated_accessions(origin,tx_ac,pro_ac);

comment on table associated_accessions is 'transcript-protein accession pairs associated in source databases';
