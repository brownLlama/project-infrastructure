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
ssh-keygen -t ed25519 -C "it@datadice.io" -f ~/.ssh/airflow -N ""
eval "$(ssh-agent -s)"
ssh-add ~/.ssh/airflow
ssh-add -l
echo -e "\n***** Public Key *****\n\n"
cat ~/.ssh/airflow.pub
echo -e "\n\n***** Public Key *****"
```

Copy the public key and then goto the git repo and add the public key under deploy keys section. For GitHub, you can find it under `Settings -> Deploy Keys -> Add deploy key`. Give a suitable title (suggestion: <PROJECT-NAME>-airflow) and then paste the public key.

## Cloning on `airflow-haproxy-vm-docker` directory

The git repo contains all infrastructure required for the whole project and here we only need `airflow-haproxy-vm-docker` directory to deploy airflow. So, to clone only this directory without cloning the whole repo, we can use sparse-checkout command. When running the following commands, if there is a prompt to add fingerprint to known hosts, then type `yes`. Also, change the variables `REPO_NAME` and `SSH-GITHUB-LINK` variables.

```bash
sudo sh -c 'echo "REPO_NAME=\"<REPO_NAME>\"" >> /etc/environment'
source /etc/environment

git clone --filter=blob:none --no-checkout <GIT_SSH_LINK>
cd "$REPO_NAME"
git sparse-checkout init
git sparse-checkout set infrastructure-artifacts/airflow-haproxy-vm-docker
git checkout
cd
```

## Setting up Airflow

It is recommended to have airflow artifacts under `srv` directory in VM and deploy airflow within that directory. We also need to install docker-compose, configure haproxy and manage other packages. To make things easy, all can be done by running `setup.sh` file.

```bash
sudo ~/"$REPO_NAME"/infrastructure-artifacts/airflow-haproxy-vm-docker/setup.sh
```

# Post Deployment

Check if everything is working running `docker ps`.

#####################################---

# Important things to do:

After setting up everything you need to do a gcloud login:

```bash
gcloud auth login
```

and then

```bash
gcloud auth configure-docker
```

in order that the `~/.docker/config.json`is going to be set up. This is important! Afterwards you can start the system.

# GCS Auto-Sync

Check where gsutil is:

```bash
which gsutil
```

We assume now that gsutil is in: `/snap/bin/gsutil`. This will be used in the gcs_sync.sh file.

Please give the gcs_sync.sh execution permissions:

```bash
sudo chmod +x gcs_sync.sh
```

Then open the crontab:

```bash
sudo crontab -e
# if you do this for the first time, it will prompt you for the editor
# personal recommendation: Use VIM, not Nano
```

Add the following line to the crontab (assuming "/srv/airflow" is the folder in which airflow and the dags reside):

```bash
*/10 * * * * /srv/airflow/gcs_sync.sh >> /srv/airflow/gcs_sync.log 2>&1
```

## Debugging

there should be a a log file beeing created in `/srv/airflow/gcs_sync.log`. Alternatively you can lookup general cron logs:

```bash
grep CRON /var/log/syslog
```

If you see no logs at all then there is something wrong in your crontab configuration

# -----------------------

uncomment line 37-39 in VM
