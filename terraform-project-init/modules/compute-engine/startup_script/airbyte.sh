#!/usr/bin/env bash

sudo apt udpate
sudo apt-get update
sudo apt-get install -y git

# Runs the Airbyte Docker container, everytimes VM restarts
sudo /srv/"$REPO_NAME"/infrastructure-artifacts/airbyte-haproxy-vm-docker/run.sh
