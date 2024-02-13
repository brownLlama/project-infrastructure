#!/usr/bin/env bash

# Shutting down system if active
./shut-down-airbyte.sh

# Building project and executing system
docker-compose up -d --build --force-recreate
