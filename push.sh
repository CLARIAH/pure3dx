#!/usr/bin/env bash

source .env
echo "pushing pure3d_author docker images; tagging as docker registry/diginfra.net/pure3d/pure3d_author:${dockertag} and :latest ...."
#
# echo "If login fails, go to registry.diginfra.net and log in and then run this script again"
docker login registry.diginfra.net

docker tag pure3d_author:${dockertag} registry.diginfra.net/pure3d/pure3d_author:${dockertag}
docker tag pure3d_author:${dockertag} registry.diginfra.net/pure3d/pure3d_author:latest
docker push registry.diginfra.net/pure3d/pure3d_author:${dockertag}
docker push registry.diginfra.net/pure3d/pure3d_author:latest
