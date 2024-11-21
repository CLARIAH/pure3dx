#!/bin/sh

if [[ "$1" == "" ]]; then
    runmode=prod
else
    runmode="$1"
fi

cd published/$runmode
python -m http.server 8080 --bind localhost
