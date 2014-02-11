create or replace view _ddl_grant_select_v as 
select concat('grant select on ',table_schema,'.',table_name,' to uta_public;') 
from information_schema.tables
where table_schema='uta1';

create or replace view _ddl_drop_views_v as
select concat('drop view if exists ',table_schema,'.',table_name,' cascade;')
  from information_schema.views where table_schema='uta1' and table_name ~ '_(v|dv)$'
UNION
select concat('drop table if exists ',table_schema,'.',table_name,' cascade;')
  from information_schema.tables where table_schema='uta1' and table_name ~ '_(mv)$' ;
