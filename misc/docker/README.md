# How to build the uta dockerfile
#################################

please replace the string uta_20170707 here with the correct version for which you would like to build.

1. push dump to minion
see uta/loading/admin.mk

2. build docker image
```
docker build -f uta.dockerfile --build-arg uta_version=uta_20170707 --rm=true -t biocommons/uta:uta_20170707 .
```

3. test it
```
docker run -v /tmp:/tmp --name uta_20170707 -p 10629:5432 biocommons/uta:uta_20170707
```

4. if successful, tag and push
```
docker tag biocommons/uta:uta_20170707 biocommons/uta
docker push biocommons/uta:uta_20170707
docker push biocommons/uta:latest
```