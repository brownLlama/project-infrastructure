# Project Infrastructure

## Introduction

Every software project requires a well-structured infrastructure to ensure smooth development, deployment, and maintenance. This document provides an overview of a typical project infrastructure.

## Project Structure

A typical project structure might look like this:

```
PROJECT-NAME
├─ custom-pip-package
│  ├─ PROJECT_NAME_utilpack
│  │  ├─ gcp_toolkit
│  │  │  └─ ...
│  │  └─ quickops_toolkit
│  │     └─ ...
│  ├─ LICENSE
│  ├─ README.md
│  └─ setup.py
├─ docker-images
│  ├─ api-integration
│  │  └─ ...
│  ├─ cloud-run
│  │  └─ ...
│  ├─ README.md
│  └─ __init__.py
├─ infrastructure
│  └─ ...
├─ terraform
│  └─ ...
├─ .darglint
├─ .flake8
├─ .gitignore
├─ .pre-commit-config.yaml
├─ CODEOWNERS
├─ README.md
└─ pyproject.toml
```

### Naming Guidelines

- Parent folders (which are not Python packages) should be named in `kebab-case`
- Python scripts and Python package folders should be named in `snake_case`

### Pre-Commits

To ensure code quality and maintain a clean repository, we use pre-commit hooks. You should set these up on your local machine. We use pre-commit hooks to check and enforce code quality standards.

#### Installation

To set up pre-commit hooks, first install the pre-commit package:

```bash
pip install pre-commit
pre install tomli
```

#### Setting up the Project

```bash
pre-commit install
```

This will install the pre-commit script in your .git/hooks/ directory, which means the checks defined in .pre-commit-config.yaml will be run automatically every time you commit changes to your code.

Please make sure to update these setups regularly to incorporate any new changes in the project configuration.

#### Updating .pre-commit-config.yaml

```bash
pre-commit run --all-files
pre-commit autoupdate
```

###################################################---

### Poetry

We recommend using Poetry for managing dependencies, but you can use whichever package manager you prefer. [Poetry](https://python-poetry.org/) is a Python dependency management tool that simplifies package management and project setup.

#### Installation

To install Poetry, open your terminal and run the following command:

```bash
pip install poetry
pip install toml-sort
```

#### Setting up the Project

```bash
# Resolve and install dependencies
poetry lock
poetry isntall
# Update all dependencies to their latest versions
poetry update
# Install important library
poetry add --dev 'black'
poetry add --dev tomli
poetry add tomli
```

These commands will ensure that your environment matches the project setup as defined in the `pyproject.toml` and `poetry.lock` files.

## Cloning the repo

To clone this repo, please use the following commands in your local machine. This will create a private and public key, which we will use it for SSH.

```bash
ssh-keygen -t ed25519 -C "it@datadice.io" -f ~/.ssh/airbyte -N ""
eval "$(ssh-agent -s)"
ssh-add ~/.ssh/airbyte
ssh-add -l
echo -e "\n***** Public Key *****\n\n"
cat ~/.ssh/airbyte.pub
echo -e "\n\n***** Public Key *****"
```

Copy the public key and then goto the github repo and under `Settings -> Deploy Keys -> Add deploy key`. Give a suitable title and then paste the public key.

Now to clone the repo, run the following commands to clone git repo. If there is a prompt to add fingerprint to known hosts, then type `yes`.

```bash
git clone <YOUR-SSH-GITHUB-LINK>
```
