#!/usr/bin/env bash

# Shutting down system if active
cd ./haproxy || exit
./shut-down-haproxy.sh
cd ..
cd ./airbyte || exit
./shut-down-airbyte.sh
cd ..
