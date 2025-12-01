#!/usr/bin/env bash

source .env
echo "building pure3d_author docker images; tagging as docker pure3d_author:${dockertag}...."
docker build --platform linux/amd64 -f Dockerfile -t pure3d_author:${dockertag} .

if [ "$?" == "0" ]; then
  echo "docker images completed ...."
  docker images | grep pure3d_author:${dockertag}
else
  echo "docker image building failed!"
  exit 1
fi
