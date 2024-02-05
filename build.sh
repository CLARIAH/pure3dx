#!/usr/bin/env bash

source .env
echo "building pure3dapp docker images from local folder; tagging as docker pure3dapp:${dockertag}...."
docker build --platform linux/amd64 -f Dockerfile -t pure3dapp:${dockertag} \
  --build-arg gitlocation=${gitlocation} \
  --build-arg gitbranch=${gitbranch} \
  --build-arg flasksecret=${flasksecret} \
  --build-arg DATA_DIR=${DATA_DIR} \
  .

if [ "$?" == "0" ]; then
  echo "docker images completed ...."
  docker images | grep pure3dapp:${dockertag}
else
  echo "docker image building failed!"
  exit 1
fi

sleep 3

echo "If login fails, go to registry.huc.knaw.nl and log in and then run this script again"
docker login registry.huc.knaw.nl

docker tag pure3dapp:${dockertag} registry.huc.knaw.nl/pure3dapp/pure3dapp:${dockertag}
docker tag pure3dapp:${dockertag} registry.huc.knaw.nl/pure3dapp/pure3dapp:latest
docker images | grep registry.huc.knaw.nl/pure3dapp/pure3dapp:${dockertag}
docker push registry.huc.knaw.nl/pure3dapp/pure3dapp:${dockertag}
docker push registry.huc.knaw.nl/pure3dapp/pure3dapp:latest
