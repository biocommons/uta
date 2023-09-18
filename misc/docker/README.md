# How to build the uta dockerfile

1. Define the version that you'd like to build. The pgdump file for
   this version must already exist at dl.biocommons.org.

```
UTA_VERSION=uta_20210129b
```


2. Build docker image
```
export uta_v=20210129b
docker build -f uta.dockerfile --build-arg uta_version=$UTA_VERSION --rm=true -t biocommons/uta:$UTA_VERSION .
```


3. Try to build a running container with the image
```
docker run -e POSTGRES_PASSWORD=password -v /tmp:/tmp -v uta_vol:/var/lib/postgresql/data --name $UTA_VERSION --network=host biocommons/uta:$UTA_VERSION
```

(`-v /tmp:/tmp` ensures that you'll reuse prior data downloads, if available)


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
docker volume rm uta_vol
```
