-- sqlalchemy + alembic was turning out to be more headache than I
-- could handle.

-- This sql pulls data from uta_20140210 into uta_1_1 (the nascent
-- schema)

set search_path = uta_1_1;

insert into origin select * from uta_20140210.origin;
select setval('origin_origin_id_seq', (select max(origin_id) from origin));

insert into gene select * from uta_20140210.gene;

insert into transcript select * from uta_20140210.transcript;

-- 25s / 156586 rows
insert into seq select * from uta_20140210.seq;

-- 38s / 164191 rows
insert into seq_anno select * from uta_20140210.seq_anno;
select setval('seq_anno_seq_anno_id_seq', (select max(seq_anno_id) from seq_anno));

-- insert into exon_set select * from uta_20140210.exon_set;
-- 20140210 didn't have an FK from exon_set to transcript
-- 33s / 338769 rows
insert into exon_set
  select ES.* from uta_20140210.exon_set ES
    join transcript T on ES.tx_ac=T.ac;
select setval('exon_set_exon_set_id_seq', (select max(exon_set_id) from exon_set));

-- 387s / 3417452 rows
insert into exon
  select E.* from uta_20140210.exon E
    join exon_set ES on E.exon_set_id=ES.exon_set_id;
select setval('exon_exon_id_seq', (select max(exon_id) from exon));

-- 5365s / 1888261 rows
insert into exon_aln
  select EA.* from uta_20140210.exon_aln EA
  where EA.tx_exon_id  in (select exon_id from exon)
    and EA.alt_exon_id in (select exon_id from exon);
select setval('exon_aln_exon_aln_id_seq', (select max(exon_aln_id) from exon_aln));

-- the BIC data had typos in the NCs in the original source data. Fix them.
update exon_set set alt_ac = 'NC_000013.10' where alt_ac = 'NC_00013.10';
update exon_set set alt_ac = 'NC_000017.10' where alt_ac = 'NC_00017.10';
