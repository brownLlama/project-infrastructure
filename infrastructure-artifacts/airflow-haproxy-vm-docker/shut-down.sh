#!/usr/bin/env bash

# Shutting down system if active
cd ./haproxy || exit
./shut-down-haproxy.sh
cd ..
cd ./airflow || exit
./shut-down-airflow.sh
cd ..
