#!/usr/bin/env bash

# Moving repo to srv directory
mv "$REPO_NAME" /srv

# Creating a self-signed certificate
openssl req -x509 -nodes -newkey rsa:2048 -keyout /etc/ssl/private/airflow-selfsigned.key -out /etc/ssl/certs/airflow-selfsigned.crt

# Copying the self-signed certificate to the airflow directory
cp /etc/ssl/private/airflow-selfsigned.key /srv/"$REPO_NAME"/infrastructure-artifacts/airflow-haproxy-vm-docker/haproxy/
cp /etc/ssl/certs/airflow-selfsigned.crt /srv/"$REPO_NAME"/infrastructure-artifacts/airflow-haproxy-vm-docker/haproxy/
# Creating a pem file
cat /srv/"$REPO_NAME"/infrastructure-artifacts/airflow-haproxy-vm-docker/haproxy/airflow-selfsigned.key /srv/"$REPO_NAME"/infrastructure-artifacts/airflow-haproxy-vm-docker/haproxy/airflow-selfsigned.crt >/srv/"$REPO_NAME"/infrastructure-artifacts/airflow-haproxy-vm-docker/haproxy/localhost-self-signed.pem

printf "\n***\n"
printf "You successfully setup the environment for airflow!"
printf "\n***\n"

printf "\n***\n"
printf "Deploying airflow by running ./run.sh"
printf "\n***\n"

cd /srv/"$REPO_NAME"/infrastructure-artifacts/airflow-haproxy-vm-docker || exit
./run.sh
