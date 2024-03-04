#!/usr/bin/env bash

mkdir -p logs plugins dags

# Shutting down system if active
./shut-down-airflow.sh

# Building project and executing system
docker-compose up -d --build --force-recreate
