#!/usr/bin/env bash

ssh pure3d.dev 'if [ -d /tmp/app ];then cd /tmp/app; source .env; sudo git checkout ${gitbranch}; sudo git pull; else sudo git clone -b ${gitbranch} ${gitlocation} /tmp/app; cd /tmp/app; fi'
scp .env pure3d.dev:/tmp/
scp src/pure3d/control/client_secrets.json pure3d.dev:/tmp/
if [ "$1" == "restart-only" ];then
  ssh pure3d.dev 'sudo mv /tmp/.env /tmp/app/.env && sudo mv /tmp/client_secrets.json /tmp/app/src/pure3d/control/ && cd /tmp/app && sudo ./restart.sh'
else
  ssh pure3d.dev 'sudo mv /tmp/.env /tmp/app/.env && sudo mv /tmp/client_secrets.json /tmp/app/src/pure3d/control/ && cd /tmp/app && sudo ./build.sh && sudo ./restart.sh'
fi