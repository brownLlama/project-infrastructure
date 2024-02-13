# Clone GitHub Repo

Assuming that the CE is created using Terraform, the next step would be create SSH key. If VM is created using Terraform, please run the following command to install and update required packages.

```bash
sudo apt udpate
sudo apt-get update
sudo apt-get install -y git subversion
```

Once the CE is running login into the VM. The first step is to clone the `airbyte-haproxy-vm-docker` directory from the github repo. To do so, a SSH key is needed to acces the GitHub Repo. By running the following commands, it will create a SSH Key and then will prompt out the public key.

```bash
ssh-keygen -t ed25519 -C "it@datadice.io" -f ~/.ssh/airbyte -N ""
eval "$(ssh-agent -s)"
ssh-add ~/.ssh/airbyte
ssh-add -l
echo -e "\n***** Public Key *****\n\n"
cat ~/.ssh/airbyte.pub
echo -e "\n\n***** Public Key *****"
```

Copy the public key and then goto the airbyte github repo and under `Settings -> Deploy Keys -> Add deploy key`. Give a suitable title (suggestion: <PROJECT-NAME>-airbyte) and then paste the public key.

Now to clone the repo, run the following commands to clone git repo. If there is a prompt to add fingerprint to known hosts, then type `yes`.

```bash
git clone <YOUR-SSH-GITHUB-LINK>
AIRBYTE_DIR=$(find . -mindepth 1 -maxdepth 1 -type d ! -name '.*' -print -quit | sed 's#.*/##')
sudo mv $AIRBYTE_DIR /srv
```

Before deploying the airbyte, please first read `README.md` in the repo that was just cloned. You will find this repo in the following path: `/srv/airbyte` in the VM.

# Deploying Airbyte

To setup all the necessary environments and deploy airbyte, run the following command.

```bash
sudo /srv/$AIRBYTE_DIR/setup.sh
```

# Post Deployment

Check if everything is working running `docker ps`.
