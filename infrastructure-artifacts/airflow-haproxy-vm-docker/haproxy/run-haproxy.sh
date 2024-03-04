#!/usr/bin/env bash

# Shutting down system if active
./shut-down-haproxy.sh

# Building project and executing system
docker-compose up -d --build --force-recreate
