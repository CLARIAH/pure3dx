#!/bin/bash

HELP='
Run Pure3D webapp, optionally start a browsing session as well.

Usage

Run it from the /src directory in the repo.

Set the env variable runmode to test if you want test mode,
and to pilot if you want pilotmode,
and to a path (including a `/` if you want custom mode,
otherwise production mode is assumed.

./start.sh
'

flaskhost="0.0.0.0"

if [[ "$flaskdebug" == "v" ]]; then
    flaskdebugarg="--debug"
else
    flaskdebugarg=""
fi

repodir="`pwd`"

if [[ ! -d "data" ]]; then
    mkdir data
fi

cd /app/src/pure3d

export flaskdebugarg
export repodir
export runmode
export FLASK_APP=index
export WERKZEUG_DEBUG_PIN=off

flask $flaskdebugarg run --host $flaskhost --port $flaskport &
pid=$!
trap "kill $pid" SIGTERM
wait "$pid"
