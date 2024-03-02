# Deploying Airflow

## Generating SSH for GitHub Repo

Once the VM is up and running, next step would be connecting the git repo. One of the safe way to connect git repo is via SSH key. First lets update the package manager and install git. If you created your VM using Terraform, you omit this command set and start with the next.

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
