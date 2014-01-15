CREATE DOMAIN strand_t AS SMALLINT
   CHECK( VALUE = -1 or VALUE = 1);


CREATE TABLE meta (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL
);


CREATE TABLE origin (
    origin_id SERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    added TIMESTAMP WITHOUT TIME ZONE NOT NULL,
    url TEXT,
    url_fmt TEXT
);
comment on table origin is 'sources of data';


CREATE TABLE dnaseq (
    dnaseq_id serial primary key,
    md5 TEXT UNIQUE,
    added TIMESTAMP WITHOUT TIME ZONE NOT NULL,
    seq TEXT
);


CREATE TABLE alias_dnaseq_origin (
    origin_id INTEGER NOT NULL
        REFERENCES origin(origin_id)
        ON UPDATE CASCADE ON DELETE CASCADE,
    dnaseq_id INTEGER NOT NULL
        REFERENCES dnaseq(dnaseq_id)
        ON UPDATE CASCADE ON DELETE CASCADE,
    alias TEXT NOT NULL,
    added TIMESTAMP WITHOUT TIME ZONE NOT NULL
);


CREATE TABLE gene (
    gene_id SERIAL PRIMARY KEY,
    hgnc TEXT NOT NULL,
    maploc TEXT,
    strand strand_t,
    descr TEXT,
    summary TEXT,
    aliases TEXT,
    added TIMESTAMP WITHOUT TIME ZONE NOT NULL
);


CREATE TABLE transcript (
    transcript_id SERIAL PRIMARY KEY,
    origin_id INTEGER NOT NULL
        REFERENCES origin(origin_id)
        ON UPDATE CASCADE ON DELETE CASCADE,
    ac TEXT NOT NULL,
    gene_id INTEGER 
        REFERENCES gene(gene_id)
        ON UPDATE CASCADE ON DELETE CASCADE,
    dnaseq_id INTEGER NOT NULL
        REFERENCES dnaseq(dnaseq_id)
        ON UPDATE CASCADE ON DELETE CASCADE,
    strand strand_t NOT NULL,
    cds_start_i INTEGER NOT NULL,
    cds_end_i INTEGER NOT NULL,
    added TIMESTAMP WITHOUT TIME ZONE NOT NULL
);


CREATE TABLE exonset (
    exonset_id serial primary key,
    transcript_id INTEGER NOT NULL
        REFERENCES transcript(transcript_id)
        ON UPDATE CASCADE ON DELETE CASCADE,
    dnaseq_id INTEGER NOT NULL
        REFERENCES dnaseq(dnaseq_id)
        ON UPDATE CASCADE ON DELETE CASCADE,
    origin_id INTEGER NOT NULL
        REFERENCES origin(origin_id)
        ON UPDATE CASCADE ON DELETE CASCADE,
    method TEXT,
    strand strand_t NOT NULL,
    added TIMESTAMP WITHOUT TIME ZONE NOT NULL
);


CREATE TABLE exon (
    exon_id serial primary key,
    exonset_id integer NOT NULL
        REFERENCES exonset(exonset_id)
        ON UPDATE CASCADE ON DELETE CASCADE,
    start_i integer NOT NULL,
    end_i integer NOT NULL,
    name TEXT
);


CREATE TABLE exon_exon_alignment (
    exon_exon_alignment_id serial primary key,
    exon_id1 integer NOT NULL
        REFERENCES exon(exon_id)
        ON UPDATE CASCADE ON DELETE CASCADE,
    exon_id2 integer NOT NULL
        REFERENCES exon(exon_id)
        ON UPDATE CASCADE ON DELETE CASCADE,
    cigar TEXT NOT NULL,
    CONSTRAINT exon_alignment_check CHECK (exon_id1 < exon_id2)
);


