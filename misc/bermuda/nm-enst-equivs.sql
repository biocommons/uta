create table nm_enst_equivs (
	   hgnc	 text not null,
	   nm 	 text not null,
	   enst	 text not null,
	   status text not null
);

create view nm_enst_equivs_flat as
select hgnc,nm,array_to_string(array_agg(format('%s/%s',enst,status) order by status = 'CC',enst),',') as enst_equivs
from nm_enst_equivs
group by hgnc,nm;
