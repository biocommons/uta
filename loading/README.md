## UTA Loading

This directory contains files for loading and releasing a new UTA database.


To build
```shell
docker-compose build
```

```shell
docker-compose up
docker exec -it uta_python bash
```

If you need to delete the containers and postgres data
```shell
docker-compose down --volumes
```

To test the connection between your localhost and the postgres database
```shell
 psql -h localhost -U anonymous -d uta -c "select * from uta_${uta_v}.meta"
```

To test the connection between uta_python and the postgres database running in the postgres container:
```shell
docker exec -it uta_python bash
PGPASSWORD=anonymous psql -h postgres -U anonymous -d uta
```

To test that uta was installed correctly:
```shell
docker exec -it uta_python bash
uta --conf=../etc/global.conf --conf=../etc/uta_dev@postgres.conf shell
```