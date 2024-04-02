#!/bin/sh

HELP="

./pages-generate.sh x y z ...

where x, y, z are integers that specify the features projects.
"

source .env

repodir="`pwd`"
cd src


if [[ "$1" == "--help" ]]; then
    printf $HELP
elif [[ "$1" == "" ]]; then
    runmode=custom
else
    runmode="$1"
    shift
fi

DATA_DIR="$repodir/data"
PUB_DIR="$repodir/published"

export repodir
export runmode
export DATA_DIR
export PUB_DIR
export PUB_URL
export AUTHOR_URL

python design.py "$@"
