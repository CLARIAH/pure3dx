#!/bin/bash

HELP="
Run Pure3D webapp, optionally start a browsing session as well.

Usage

Run it from the /src directory in the repo.

./start.sh [test|prod]
./start.sh
    Test mode

./start.sh prod
    Production mode
"

flaskdebug=""
flasktest=""
flaskhost="0.0.0.0"
flaskport="8000"
browse="x"

while [ ! -z "$1" ]; do
    if [[ "$1" == "--help" ]]; then
        printf "$HELP\n"
        exit 0
    fi
    if [[ "$1" == "prod" ]]; then
        flaskdebug=""
        flasktest=""
        shift
    elif [[ "$1" == "test" ]]; then
        flaskdebug="--debug"
        flasktest="test"
        shift
    else
        flaskport="$1"
        shift
        break
    fi
done


cd ..
repodir="`pwd`"

if [[ ! -d "data" ]]; then
    mkdir data
fi

cd src/pure3d

export flasktest
export flaskdebug
export flaskport
export repodir
export FLASK_APP=index

flask $flaskdebug run --host $flaskhost --port $flaskport &
pid=$!
trap "kill $pid" SIGTERM
wait "$pid"
