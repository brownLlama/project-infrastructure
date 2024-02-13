#!/usr/bin/env bash

cd ~ || exit
AIRBYTE_DIR=$(find . -mindepth 1 -maxdepth 1 -type d ! -name '.*' -print -quit | sed 's#.\_/##')
sudo mv "$AIRBYTE_DIR" /srv
sudo /srv/"$AIRBYTE_DIR"/infrastructure-artifacts/airbyte-haproxy-vm-docker/setup.sh

apt remove docker docker-engine docker.io containerd runc
apt update

apt install \
	ca-certificates \
	curl \
	gnupg \
	lsb-release \
	acl

curl -fsSL https://download.docker.com/linux/debian/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg

echo \
	"deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/debian \
  $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list >/dev/null

apt update
apt install docker.io docker-ce docker-ce-cli containerd.io

curl -L "https://github.com/docker/compose/releases/download/1.29.2/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
chmod +x /usr/local/bin/docker-compose

gcloud auth configure-docker

apt install docker.io

service docker start

chmod 777 /var/run/docker.sock

sed -i 's|docker.com/linux/debian|docker.com/linux/ubuntu|g' /etc/apt/sources.list
apt update

export VISUAL=vim
export EDITOR=vim

# Creating a self-signed certificate
openssl req -x509 -nodes -newkey rsa:2048 -keyout /etc/ssl/private/airbyte-selfsigned.key -out /etc/ssl/certs/airbyte-selfsigned.crt

# Copying the self-signed certificate to the airbyte directory
cp /etc/ssl/private/airbyte-selfsigned.key "/srv/$AIRBYTE_DIR/infrastructure-artifacts/airbyte-haproxy-vm-docker/haproxy/"
cp /etc/ssl/certs/airbyte-selfsigned.crt "/srv/$AIRBYTE_DIR/infrastructure-artifacts/airbyte-haproxy-vm-docker/haproxy/"
# Creating a pem file
cat "/srv/$AIRBYTE_DIR/infrastructure-artifacts/airbyte-haproxy-vm-docker/haproxy/airbyte-selfsigned.key" "/srv/$AIRBYTE_DIR/infrastructure-artifacts/airbyte-haproxy-vm-docker/haproxy/airbyte-selfsigned.crt" >"/srv/$AIRBYTE_DIR/infrastructure-artifacts/airbyte-haproxy-vm-docker/haproxy/localhost-self-signed.pem"

echo "You successfully setup the environment for airbyte!"
echo "Deploying Airbyte by running ./run.sh"
