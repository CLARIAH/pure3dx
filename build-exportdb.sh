#!/usr/bin/env bash

source .env
echo "building pure3d_exportdb docker images from local folder; tagging as docker pure3d_exportdb:${dockertag}...."
docker build --platform linux/amd64 -f Dockerfile-exportdb -t pure3d_exportdb:${dockertag} .

if [ "$?" == "0" ]; then
  echo "docker images completed ...."
  docker images | grep pure3d_exportdb:${dockertag}
else
  echo "docker image building failed!"
  exit 1
fi

sleep 3

echo "If login fails, go to registry.diginfra.net and log in and then run this script again"
docker login registry.diginfra.net

docker tag pure3d_exportdb:${dockertag} registry.diginfra.net/pure3d/pure3d_exportdb:${dockertag}
docker tag pure3d_exportdb:${dockertag} registry.diginfra.net/pure3d/pure3d_exportdb:latest
docker images | grep registry.diginfra.net/pure3d/pure3d_exportdb:${dockertag}
docker push registry.diginfra.net/pure3d/pure3d_exportdb:${dockertag}
docker push registry.diginfra.net/pure3d/pure3d_exportdb:latest
