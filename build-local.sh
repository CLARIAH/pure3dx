#!/usr/bin/env bash

source .env
echo "building pure3d_author docker images from local folder; tagging as docker pure3d_author:${dockertag}...."
docker build -f Dockerfile -t pure3d_author:${dockertag}-loc .

if [ "$?" == "0" ]; then
  echo "docker images completed ...."
  docker images | grep pure3d_author:${dockertag}-loc
else
  echo "docker image building failed!"
  exit 1
fi

sleep 3

docker login
docker tag pure3d_author:${dockertag}-loc pure3d_author:latest-loc
