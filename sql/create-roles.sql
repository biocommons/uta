create role uta_admin  login;
create role uta_public login;
create role anonymous  login;
create role reece      login;

-- enable 'set role uta_admin', etc.
grant uta_admin to postgres;	-- required so that postgres can create db owned by uta_admin
grant postgres to reece;
grant uta_admin to reece;
