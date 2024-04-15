#!/bin/bash

cd ..

if [[ -f .env ]]; then
    source .env
else
    cat .env
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
# Now: backup to hucdrive

readonly budate="$(date '+%Y-%m-%d')"
readonly budiscarddate="$(date -d '-7 days' '+%Y-%m-%d')"

function myscp {
    src="$1"
    shift
    dst="$1"
    shift
    scp -q -O -r "$@" -i ../secret/id_rsa -o "StrictHostKeyChecking no" -P 2222 "$src" "${backupuser}@${backuphost}:/${backupauthor}/$dst"
}

function mysftp {
    cmd="$1"
    shift
    printf "$cmd\n" | sftp -q "$@" -i ../secret/id_rsa -o "StrictHostKeyChecking no" -P 2222 "${backupuser}@${backuphost}:/${backupauthor}" | tail -n +2
}

printf "Make full backup of today: ${budate} ...\n"
srcdata="$DATA_DIR/working/prod"
myscp "$srcdata" "$budate"

buall=`mysftp ls` 
printf "Done. All backups:\n$buall\n"

printf "Discard old backups ...\n"

for d in $buall
do
    if [[ "$d" < "$budiscarddate" ]]; then
        mysftp "rmdir ${d}"
        printf "$d removed\n"
    else
        printf "$d retained\n"
    fi
done

printf "Done. Remaining backups:\n"
mysftp ls

# End external backup action
