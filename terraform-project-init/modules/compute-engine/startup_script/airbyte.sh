#!/usr/bin/env bash

sudo apt udpate
sudo apt-get update
sudo apt-get install -y git

REPO_NAME="<REPO_NAME>"
# Runs the Airbyte Docker container, everytimes VM restarts
sudo /srv/"$REPO_NAME"/infrastructure-artifacts/airbyte-haproxy-vm-docker/run.sh
