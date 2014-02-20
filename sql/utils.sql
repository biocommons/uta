create or replace function _create_ddl_make_schema_entities_public_ro(s text)
returns setof text
language sql strict immutable as
$$
  select concat('grant usage on schema ',s,' to PUBLIC;')
union all
  select concat('grant select on ',schemaname,'.',tablename,' to PUBLIC;') from pg_tables where schemaname=s
union all
  select concat('grant select on ',schemaname,'.',viewname,' to PUBLIC;') from pg_views where schemaname=s
union all
  select concat('grant select on ',schemaname,'.',matviewname,' to PUBLIC;') from pg_matviews where schemaname=s
union all
  select concat('grant execute on function ',n.nspname,'.',p.proname,'(',pg_catalog.pg_get_function_arguments(p.oid),') to PUBLIC;' FROM pg_catalog.pg_proc p LEFT JOIN pg_catalog.pg_namespace n ON n.oid = p.pronamespace where n.nspname=s
;
$$;

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
