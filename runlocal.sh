#!/bin/bash

app=$K_NAMESPACE
approot="$K_LOCALDIR"

HELP="

Run local app $app

USAGE

runlocal [host|up|down|peek|peekpub|mongo|buildlocal|build|dev] args
"

cd $approot

source .env

function apphost {
    rdctl start --virtual-machine.memory-in-gb 6
}

function appup {
    # start the app, including its services

    apphost

    flaskdebug="x"
    runmode=""
    good="v"

    while [ ! -z "$1" ]; do
        if [[ "$1" == "prod" ]]; then
            runmode="prod"
            shift
        elif [[ "$1" == "test" ]]; then
            runmode="test"
            shift
        elif [[ "$1" == "pilot" ]]; then
            runmode="pilot"
            shift
        elif [[ "$1" == "custom" ]]; then
            runmode="custom"
            shift
        elif [[ "$1" == "nodebug" ]]; then
            flaskdebug="x"
            shift
        elif [[ "$1" == "debug" ]]; then
            flaskdebug="v"
            shift
        else
            echo "unrecognized argument '$1'"
            good="x"
            shift
        fi
    done

    if [[ "$runmode" == "" ]]; then
        echo "runmode not set to either prod, test, pilot, or custom"
        good="x"
    fi


    if [[ "$good" == "v" ]]; then
        export runmode
        export flaskdebug
        docker compose up -d
        docker compose logs -f
        docker compose down
    fi
}

function appdown {
    # stop the app, including its services (mongod)
    # mostly not needed, because we end appup with Ctrl+C
    docker compose down
}

function apppeek {
    # shell into the running app locally
    docker exec -e COLUMNS="`tput cols`" -e LINES="`tput lines`" -it ${app}_author /bin/bash -l
}

function apppeekpub {
    # shell into the running app locally
    docker exec -e COLUMNS="`tput cols`" -e LINES="`tput lines`" -it ${app}_pub /bin/bash -l
}

function appmongo {
    # open the host mongo client and connect to the mongod service of the app
    runmode=""
    good="v"

    while [ ! -z "$1" ]; do
        if [[ "$1" == "prod" ]]; then
            runmode="prod"
            shift
        elif [[ "$1" == "test" ]]; then
            runmode="test"
            shift
        elif [[ "$1" == "pilot" ]]; then
            runmode="pilot"
            shift
        elif [[ "$1" == "custom" ]]; then
            runmode="custom"
            shift
        else
            echo "unrecognized argument '$1'"
            good="x"
            shift
        fi
    done

    if [[ "$runmode" == "" ]]; then
        mongosh --port $mongoportouter -u $mongouser -p $mongopassword --authenticationDatabase admin
    else
        echo mongosh --port $mongoportouter -u root -p example --authenticationDatabase admin ${app}_$runmode
        mongosh --port $mongoportouter -u $mongouser -p $mongopassword --authenticationDatabase admin ${app}_$runmode
    fi
}

function appbuildlocal {
    # build the app locally, using local github clone as is
    # if you pass "push" as argument, the docker images will be pushed to the
    # registry
    ./build-local.sh "$@"
}

function appbuild {
    # build the app for kubernetes, using local github clone as is
    # if you pass "push" as argument, the docker images will be pushed to the
    # registry
    ./build-local.sh "$@"
}

function appdev {
    # build the app on the dev machine, i.e.
    # on the dev machine: clone the repo,
    # and, unless "restart-only" is passed, build the docker image
    # and restart the app
    ./start.sh "$@"
}

command="$1"

if [ -z "$1" ]; then
    echo "no command given"
    printf "$HELP"
    exit
elif [ "$1" == "--help" ]; then
    printf "$HELP"
    exit
fi

command="$1"
shift

app$command "$@"
