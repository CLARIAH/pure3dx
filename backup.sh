#!/bin/bash
#
# on linux: 
#   date -d "-30 days" '+%Y-%m-%d'
# macos
#   date -v "-30d" '+%Y-%m-%d'

BACKUP_DIR=~/Downloads/backups

# make empty backup directories

mkdir -p $BACKUP_DIR

for i in {10..40}; do
    mkdir -p $BACKUP_DIR/`date -v -${i}d '+%Y-%m-%dT%H-%M-%S'`
done

ls -l $BACKUP_DIR

# weed out the directories with dates longer than 30 days ago

CUT_OFF=`date -v "-30d" '+%Y-%m-%d'`

for d in `ls $BACKUP_DIR`; do
    if [[ "$d" < "$CUT_OFF" ]]; then
        rm -rf "$BACKUP_DIR/$d"
        echo "$d removed"
    else
        echo "$d retained"
    fi
done
