create view _grant_commands_v as 
select concat('grant select on ',table_schema,'.',table_name,' to uta_public;') 
from information_schema.tables
where table_schema='uta1';

