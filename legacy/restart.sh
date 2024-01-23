#!/usr/bin/env bash

source .env
docker pull registry.diginfra.net/vicd/pure3dapp:${dockertag}
docker-compose --env-file .env -f docker-compose-acc.yml down
sleep 1
docker-compose --env-file .env -f docker-compose-acc.yml up -d
