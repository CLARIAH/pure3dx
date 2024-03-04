#!/usr/bin/env bash

source .env
echo "building pure3d_edit docker images from local folder; tagging as docker pure3d_edit:${dockertag}...."
docker build --platform linux/amd64 -f Dockerfile -t pure3d_edit:${dockertag} \
  --build-arg gitlocation=${gitlocation} \
  --build-arg gitbranch=${gitbranch} \
  --build-arg flasksecret=${flasksecret} \
  --build-arg DATA_DIR=${DATA_DIR} \
  --build-arg PUB_DIR=${PUB_DIR} \
  .

if [ "$?" == "0" ]; then
  echo "docker images completed ...."
  docker images | grep pure3d_edit:${dockertag}
else
  echo "docker image building failed!"
  exit 1
fi

sleep 3

echo "If login fails, go to registry.huc.knaw.nl and log in and then run this script again"
docker login registry.huc.knaw.nl

docker tag pure3d_edit:${dockertag} registry.huc.knaw.nl/pure3d/pure3d_edit:${dockertag}
docker tag pure3d_edit:${dockertag} registry.huc.knaw.nl/pure3d/pure3d_edit:latest
docker images | grep registry.huc.knaw.nl/pure3d/pure3d_edit:${dockertag}
docker push registry.huc.knaw.nl/pure3d/pure3d_edit:${dockertag}
docker push registry.huc.knaw.nl/pure3d/pure3d_edit:latest
