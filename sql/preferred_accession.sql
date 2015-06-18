create table preferred_accession (
    preferred_accession_id serial primary key,
    hgnc text not null,
    tx_ac text unique,
    pro_ac text,
    origin text not null,
    added timestamp with time zone not null default now()
    );

create index preferred_accession_hgnc on preferred_accession(hgnc);
