-- drop table gtx_alignment;
-- drop table transcript_exon;
-- drop table genomic_exon;
-- drop table transcript;
-- drop table gene;


create table gene (
       gene text primary key,
       chr text not null,
       strand smallint not null,
       start_i int not null,
       end_i int not null,
       maploc text,
       descr text,
       summary text,
	   added timestamptz not null default now(),

       constraint "start_i-lt-end_i" check (start_i < end_i)       
);

create table transcript (
       ac text primary key,
       gene text not null
            references gene(gene) on update cascade on delete cascade,
       cds_start_i int not null,
       cds_end_i int not null,
	   added timestamptz not null default now(),
       seq text,

       constraint "cds_start_i-lt-cds_end_i" check (cds_start_i < cds_end_i)
);

create table genomic_exon (
       genomic_exon_id serial primary key,
       ac text not null
            references transcript(ac) on update cascade on delete cascade,
       start_i int not null,
       end_i int not null,
       ord smallint NOT NULL,

       constraint "ge-ord-unique-per-ac" unique (ac,ord),
       constraint "start_i-lt-end_i" check (start_i < end_i)       
);

create table transcript_exon (
       transcript_exon_id serial primary key,
       ac text not null
            references transcript(ac) on update cascade on delete cascade,
       start_i int not null,
       end_i int not null,
       ord smallint NOT NULL,
       name text,

       constraint "te-ord-unique-per-ac" unique (ac,ord),
       constraint "start_i-lt-end_i" check (start_i < end_i)
);

create table gtx_alignment (
       genomic_exon_id int not null 
            references genomic_exon(genomic_exon_id) on update cascade on delete cascade,
       transcript_exon_id int not null 
            references transcript_exon(transcript_exon_id) on update cascade on delete cascade,
       cigar text not null,
       seqviewer_url text
);

create table nm_enst_equiv (
       ac text not null,
       enst text not null,
       status text not null,
       constraint "ac-enst-unique" unique (ac,enst)
);
