CREATE TABLE exon (
    exon_id serial primary key,
    transcript_id integer NOT NULL,
    start_i integer NOT NULL,
    end_i integer NOT NULL,
    name TEXT,
    seq TEXT
);

CREATE TABLE exon_alignment (
    exon_alignment_id serial primary key,
    exon_id1 integer NOT NULL,
    exon_id2 integer NOT NULL,
    cigar TEXT NOT NULL,
    alignment TEXT,
    CONSTRAINT exon_alignment_check CHECK (exon_id1 < exon_id2)
);

CREATE TABLE gene (
    gene_id serial primary key,
    added timestamp without time zone NOT NULL,
    gene TEXT NOT NULL,
    maploc TEXT,
    strand smallint,
    descr TEXT,
    summary TEXT,
    CONSTRAINT strand_is_plus_or_minus_1 CHECK (strand = -1 OR strand = 1)
);

CREATE TABLE meta (
    key TEXT NOT NULL,
    value TEXT NOT NULL
);

CREATE TABLE nseq (
    nseq_id serial primary key,
    origin_id integer NOT NULL,
    ac TEXT NOT NULL,
    added timestamp without time zone NOT NULL,
    md5 TEXT,
    seq TEXT
);

CREATE TABLE origin (
    origin_id serial primary key,
    name TEXT NOT NULL,
    added timestamp without time zone NOT NULL,
    url TEXT,
    url_fmt TEXT
;

CREATE TABLE origin_transcript_alias (
    transcript_id serial primary key,
    origin_id integer NOT NULL,
    nseq_id integer NOT NULL,
    added timestamp without time zone NOT NULL,
    gene TEXT,
    gene_id integer
);

CREATE TABLE transcript (
    transcript_id serial primary key,
    nseq_id integer NOT NULL,
    added timestamp without time zone NOT NULL,
    strand smallint NOT NULL,
    cds_start_i integer NOT NULL,
    cds_end_i integer NOT NULL,
    CONSTRAINT strand_is_plus_or_minus_1 CHECK (strand = -1 OR strand = 1)
);
