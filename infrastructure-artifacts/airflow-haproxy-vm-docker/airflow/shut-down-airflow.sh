#!/usr/bin/env bash

echo "Shutting down containers & cleaning up: "
docker-compose down
screen -X -S loggingSession quit
screen -wipe
