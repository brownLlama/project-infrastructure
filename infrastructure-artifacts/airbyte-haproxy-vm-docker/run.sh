#!/usr/bin/env bash

./shut-down.sh

cd ./airbyte || exit
./run-airbyte.sh
cd ..
cd ./haproxy || exit
./run-haproxy.sh
cd ..
