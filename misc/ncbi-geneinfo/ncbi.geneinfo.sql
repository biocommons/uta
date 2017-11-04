create table geneinfo (
       gene_id integer primary key,
       tax_id integer not null,
       hgnc text,
       maploc text,
       aliases text,
       type text,
       summary text,
       descr text,
       xrefs text
       );
       

