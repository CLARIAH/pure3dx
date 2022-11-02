#!/bin/bash

HELP="
Restores example data to data directory
Resets mongodb data and imports data from file system into mongodb.

Pass tasks to indicate what should be imported:

content
    Imports content from the file system and fills MongoDb tables
    accordingly.

    The content should have been provisioned to the container before,
    by

    ./provision.sh content

    in the top-level of the repo.

Usage

Run it from the /src directory in a running container.

./import.sh [task] [task] ...

"

docontent="x"

while [ ! -z "$1" ]; do
    if [[ "$1" == "--help" ]]; then
        printf "$HELP\n"
        exit 0
    fi
    if [[ "$1" == "content" ]]; then
        docontent="v"
        shift
    else
        echo "unrecognized argument '$1'"
        shift
    fi
done


cd ..
repodir="`pwd`"
export repodir

cd src

if [[ "$docontent" == "v" ]]; then
    echo "Filling mongodb collections ..."
    python3 pure3d/import.py content
    echo "Done"
fi
