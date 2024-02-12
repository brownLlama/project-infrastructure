#!/bin/bash

sudo apt udpate
sudo apt-get update

sudo apt-get install -y git
sudo apt install xclip

# Runs the Airbyte Docker container, everytimes VM restarts
sudo /srv/airbyte/run.sh
