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
