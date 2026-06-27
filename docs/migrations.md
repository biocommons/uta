# Migrations
UTA uses alembic to manage database migrations. To auto-generate a migration:
```
alembic -c etc/alembic.ini revision --autogenerate -m "description of the migration"
```
This will create a migration script in the alembic/versions directory.
Adjust the upgrade and downgrade function definitions. To apply the migration:
```
alembic -c etc/alembic.ini upgrade head
```
To reverse a migration, use `downgrade` with the number of steps to reverse. For example, to reverse the last:
```
alembic -c etc/alembic.ini downgrade -1
```
