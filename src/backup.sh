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

python migrate.py prod -

# Begin external backup action
#
# Later: Borg statements to backup $DATA_DIR/working/prod to a backup repository
# Now: a simple copy action

burepo=~/Downloads/pure3dbackup
budata=~/github/CLARIAH/pure3dx/data/working/prod

mkdir -p $burepo
cp -R $budata $burepo
#
# End external backup action
