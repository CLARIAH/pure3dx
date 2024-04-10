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

# Begin external restore action
#
# Later: Borg statements to backup $DATA_DIR/working/prod to a backup repository
# Now: a simple copy action

burepo=~/Downloads/pure3dbackup
budata=~/github/CLARIAH/pure3dx/data/working/prod

# End external restore action


python migrate.py - prod
