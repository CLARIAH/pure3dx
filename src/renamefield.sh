#!/bin/sh

cd ..

if [ -f .env ]; then
    source .env
fi

repodir="`pwd`"
cd src

DATA_DIR="$repodir/data"

export repodir
export DATA_DIR
export mongohost
export mongoport
export mongoportouter
export mongouser
export mongopassword

python renamefield.py "$@"
