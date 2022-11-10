#!/bin/bash

HELP="
Put additional data within reach of the container.

This can be run on the host, without the need of a running container.
Although it can be performed when the container is running,
the container will see the changes.

It can provision the following kinds of data, steered by a list of
task arguments:

content
    Example data. Example data is a directory with data and additional
    yaml files. Before the app can make use of it,
    it has to be imported from within a running container by 
    
    ./import.sh content

    which populates a MongoDb.

viewers
    Client-side code of 3d viewers. This is a directory
    that needs no further processing within the container.


Usage

Run it from the toplevel directory in the repo.

./provision.sh [task] [task] ...
"

docontent="x"
doviewers="x"

while [ ! -z "$1" ]; do
    if [[ "$1" == "--help" ]]; then
        printf "$HELP\n"
        exit 0
    fi
    if [[ "$1" == "content" ]]; then
        docontent="v"
        shift
    elif [[ "$1" == "viewers" ]]; then
        doviewers="v"
        shift
    else
        echo "unrecognized argument '$1'"
        shift
    fi
done

if [[ "$docontent" == "v" ]]; then
    echo "Provisioning example data ..."
    mkdir -p data
    echo 'Copying stuff in pure3d-data/exampledata to pure3dx/data'
    if [[ -d "data/exampledata" ]]; then
        rm -rf data/exampledata
    fi
    cp -r ../pure3d-data/exampledata data/
    echo "Done"
fi

if [[ "$doviewers" == "v" ]]; then
    echo "Provisioning client code of 3d viewers ..."
    mkdir -p data
    echo 'Copying directory pure3d-data/viewers to pure3dx/data'
    if [[ -d "data/viewers" ]]; then
        rm -rf data/viewers
    fi
    cp -r ../pure3d-data/viewers data/
    echo "Done"
fi
