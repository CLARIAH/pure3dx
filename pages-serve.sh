#!/bin/sh

cd published/$1
python -m http.server 8060
