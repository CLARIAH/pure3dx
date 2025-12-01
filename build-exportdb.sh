#!/usr/bin/env bash

source .env
echo "pushing pure3d_exportdb docker images from local folder; tagging as docker pure3d_exportdb:${dockertag}...."

echo "If login fails, go to registry.diginfra.net and log in and then run this script again"
docker login registry.diginfra.net

docker tag pure3d_exportdb:${dockertag} registry.diginfra.net/pure3d/pure3d_exportdb:${dockertag}
docker tag pure3d_exportdb:${dockertag} registry.diginfra.net/pure3d/pure3d_exportdb:latest
docker push registry.diginfra.net/pure3d/pure3d_exportdb:${dockertag}
docker push registry.diginfra.net/pure3d/pure3d_exportdb:latest
