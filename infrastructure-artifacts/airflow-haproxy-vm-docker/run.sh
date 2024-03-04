#!/usr/bin/env bash

./shut-down.sh

cd ./airflow || exit
./run-airflow.sh
cd ..
cd ./haproxy || exit
./run-haproxy.sh
cd ..
