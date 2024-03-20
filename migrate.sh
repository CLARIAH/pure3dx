#!/bin/sh

cd src
cd ..
source .env

repodir="`pwd`"
cd src


DATA_DIR="$repodir/data"

export repodir
export DATA_DIR
export mongouser
export mongopassword

python migrate.py "$@"
