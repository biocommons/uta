# How to build the uta dockerfile
#################################

please replace the string uta_20170707 here with the correct version for which you would like to build.


1. Push dump to minion
see uta/loading/admin.mk


2. Build docker image
```
UTA_VERSION=uta_20180821
docker build -f uta.dockerfile --build-arg uta_version=$UTA_VERSION --rm=true -t biocommons/uta:$UTA_VERSION .
```


3. Try to build a running container with the image
```
docker run -v /tmp:/tmp -v uta_data:/usr/lib/postgresql/data --name $UTA_VERSION --network=host biocommons/uta:$UTA_VERSION
```

`-v /tmp:/tmp` ensures that you'll reuse prior data downloads, if available


4. If successful, tag and push
```
docker tag biocommons/uta:$UTA_VERSION biocommons/uta
docker push biocommons/uta:$UTA_VERSION
docker push biocommons/uta:latest
```



5. Reset!
To start over on the above:

```
docker kill $UTA_VERSION
docker rm $UTA_VERSION
docker volume rm uta_data
```
