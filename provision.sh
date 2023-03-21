#!/bin/bash

HELP="
Put additional data within reach of the container.

This can be run on the host, without the need of a running container.

It can provision the following kinds of data, steered by a list of
task arguments:

content
    Example data. Example data is a directory with data and additional
    yaml files.

viewers
    Client-side code of 3d viewers. This is a directory
    that needs no further processing within the container.

There are also flag arguments:

--resetexample
    Will delete the the working example data

--resetpilot
    Will delete the the working pilot data

When the pure3d app starts with non-existing pilot or empty data,
it will collect the data from the provisioned directory and initialize
the relevant MongoDb database accordingly.

Usage

Run it from the toplevel directory in the repo.

./provision.sh [flag or task] [flag or task] ...
"

fromloc="."
toloc="../pure3dx/data"

docontent="x"
doviewers="x"
resetexample="x"
resetpilot="x"

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
    elif [[ "$1" == "--resetexample" ]]; then
        doresetexample="v"
        shift
    elif [[ "$1" == "--resetpilot" ]]; then
        doresetpilot="v"
        shift
    else
        echo "unrecognized argument '$1'"
        shift
    fi
done

if [[ "$docontent" == "v" ]]; then
    echo "Provisioning example and pilot data ..."
    mkdir -p $toloc
    echo "Copying stuff in $fromloc/*data to $toloc"
    for key in exampledata pilotdata
    do
        if [[ -d $toloc/$key ]]; then
            rm -rf $toloc/$key
        fi
        cp -r $fromloc/$key $toloc/
    done
    echo "Done"
fi

if [[ "$doviewers" == "v" ]]; then
    echo "Provisioning client code of 3d viewers ..."
    mkdir -p data
    echo 'Copying directory pure3d-data/viewers to pure3dx/data'
    if [[ -d $toloc/viewers ]]; then
        rm -rf $toloc/viewers
    fi
    cp -r $fromloc/viewers $toloc/
    echo "Done"
fi

if [[ "$doresetexample" == "v" ]]; then
    echo "Resetting example data ..."
    workingdir=$toloc/working/test
    if [[ -e "$workingdir" ]]; then
        rm -rf "$workingdir"
    fi
    echo "Done"
fi

if [[ "$doresetpilot" == "v" ]]; then
    echo "Resetting pilot data ..."
    workingdir=$toloc/working/pilot
    if [[ -e "$workingdir" ]]; then
        rm -rf "$workingdir"
    fi
    echo "Done"
fi
