#!/usr/bin/env bash

source .env
echo "building pure3dapp docker images from local folder; tagging as docker pure3dapp:${dockertag}...."
docker build -f Dockerfile.local -t pure3dapp:${dockertag}-loc \
  --build-arg gitlocation=${gitlocation} \
  --build-arg gitbranch=${gitbranch} \
  --build-arg flasksecret=${flasksecret} \
  --build-arg DATA_DIR=${DATA_DIR} \
  .

if [ "$?" == "0" ]; then
  echo "docker images completed ...."
  docker images | grep pure3dapp:${dockertag}-loc
else
  echo "docker image building failed!"
  exit 1
fi

sleep 3

docker login
docker tag pure3dapp:${dockertag}-loc pure3dapp:latest-loc
