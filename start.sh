#!/usr/bin/env bash

scp .env pure3d.dev:/tmp/
scp src/pure3d/control/client_secrets.json pure3d.dev:/tmp/
ssh pure3d.dev 'source /tmp/.env && if [ -d /tmp/app ];then cd /tmp/app; source .env; sudo git checkout ${gitbranch}; sudo git pull; else sudo git clone -b ${gitbranch} ${gitlocation} /tmp/app; cd /tmp/app; fi && sudo mv /tmp/.env /tmp/app/.env && sudo mv /tmp/client_secrets.json /tmp/app/src/pure3d/control/'
ssh pure3d.dev 'if [ -d /tmp/pure3d-data ];then sudo git clone https://github.com/CLARIAH/pure3d-data.git /tmp/pure3d-data; else cd /tmp/pure3d-app; sudo git stash; sudo git pull; fi && cd /tmp/app && sudo ./provision.sh content viewers'

if [ "$1" == "restart-only" ];then
  ssh pure3d.dev 'cd /tmp/app && sudo ./restart.sh'
else
  ssh pure3d.dev 'cd /tmp/app && sudo ./build.sh && sudo ./restart.sh'
fi