#!/bin/sh

cd src
pushd ..

repodir="`pwd`"
popd


if [[ "$1" == "" ]]; then
    runmode=pilot
else
    runmode="$1"
fi

DATA_DIR="$repodir/data"
PUB_DIR="$repodir/published"

export repodir
export runmode
export DATA_DIR
export PUB_DIR

python design.py
