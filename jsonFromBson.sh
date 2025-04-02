#!/usr/bin/env bash

# converts all bson files in current dir to json files
# in ../json

if [[ ! -e ../json ]]; then
    mkdir ../json
fi

for fl in *.bson
do
    basenm=$(basename -- "$fl")
    fname="${basenm%.*}"
    echo "$fl => ../json/$fname.json"
    bsondump --pretty --outFile "../json/$fname.json" "$fl"
done
