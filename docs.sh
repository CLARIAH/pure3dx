#!/bin/bash

HELP="
Build and publish API docs with pdoc3.

This can be run on the host, without the need of a running container.

It is steered by the following task arguments:

build
    Build the docs and store them in the top-level site directory,
    which is in the .gitignore file.
    A count of the lines of code will be performed.

ship
    Publishes the contents of the site directory
    to the gh-pages branch on GitHub.
    Does not build, that should have been done before this step.

Usage

Run it from the toplevel directory in the repo.

./docs.sh [task] [task] ...
"

dobuild="x"
doship="x"

while [ ! -z "$1" ]; do
    if [[ "$1" == "--help" ]]; then
        printf "$HELP\n"
        exit 0
    fi
    if [[ "$1" == "build" ]]; then
        dobuild="v"
        shift
    elif [[ "$1" == "ship" ]]; then
        doship="v"
        shift
    else
        echo "unrecognized argument '$1'"
        shift
    fi
done

if [[ "$dobuild" == "v" ]]; then
    echo "Building api docs ..."
    cloc --md --out=stats.md src
    python3 apidocs.py build
    echo "Done"
fi

if [[ "$doship" == "v" ]]; then
    echo "Publishing api docs on GitHub ..."
    python3 apidocs.py ship
    echo "Done"
fi
