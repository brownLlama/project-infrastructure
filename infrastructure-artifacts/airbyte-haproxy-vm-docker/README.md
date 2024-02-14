# Deploying Airbyte

## Generating SSH for GitHub Repo

Once the VM is up and running, next step would be connecting the git repo. One of the safe way to connect git repo is via SSH key. First lets update the package manager and install git.

```bash
sudo apt udpate
sudo apt-get update
sudo apt-get install -y git
```

Let's create a SSH key by running the following commands. It will create a SSH Key and then will prompt out the public key.

```bash
ssh-keygen -t ed25519 -C "it@datadice.io" -f ~/.ssh/airbyte -N ""
eval "$(ssh-agent -s)"
ssh-add ~/.ssh/airbyte
ssh-add -l
echo -e "\n***** Public Key *****\n\n"
cat ~/.ssh/airbyte.pub
echo -e "\n\n***** Public Key *****"
```

Copy the public key and then goto the git repo and add the public key under deploy keys section. For GitHub, you can find it under `Settings -> Deploy Keys -> Add deploy key`. Give a suitable title (suggestion: <PROJECT-NAME>-airbyte) and then paste the public key.

## Cloning on `airbyte-haproxy-vm-docker` directory

The git repo contains all infrastructure required for the whole project and here we only need `airbyte-haproxy-vm-docker` directory to deploy airbyte. So, to clone only this directory without cloning the whole repo, we can use sparse-checkout command. When running the following commands, if there is a prompt to add fingerprint to known hosts, then type `yes`. Also, change the variables `REPO_NAME` and `SSH-GITHUB-LINK` variables.

```bash
REPO_NAME="<REPO_NAME>"
SSH_GITHUB_LINK="<SSH_GITHUB_LINK>"

git clone --filter=blob:none --no-checkout "$SSH_GITHUB_LINK"
cd "$REPO_NAME"
git sparse-checkout init
git sparse-checkout set infrastructure-artifacts/airbyte-haproxy-vm-docker
git checkout
cd
```

## Setting up Airbyte

It is recommended to have airbyte artifacts under `srv` directory in VM and deploy airbyte within that directory. We also need to install docker-compose, configure haproxy and manage other packages. To make things easy, all can be done by running `setup.sh` file.

```bash
sudo ~/"$REPO_NAME"/infrastructure-artifacts/airbyte-haproxy-vm-docker/setup.sh
```

# Post Deployment

Check if everything is working running `docker ps`.
