#!/bin/bash

HELP="
Run Pure3D webapp, optionally start a browsing session as well.

Usage

Run it from the /src directory in the repo.

Set the env variable runmode to test if you want test mode,
otherwise production mode is assumed.

./start.sh
"

flaskdebug=""
flasktest=""
flaskhost="0.0.0.0"

if [[ "$runmode" == "test" ]]; then
    flaskdebug="--debug"
    flasktest="test"
else
    flaskdebug=""
    flasktest=""
fi


cd ..
repodir="`pwd`"

if [[ ! -d "data" ]]; then
    mkdir data
fi

cd src/pure3d

export flasktest
export flaskdebug
export repodir
export FLASK_APP=index

flask $flaskdebug run --host $flaskhost --port $flaskport &
pid=$!
trap "kill $pid" SIGTERM
wait "$pid"
