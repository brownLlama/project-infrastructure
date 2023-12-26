# PROJECT_NAME

This repository contains the data infrastrucutre artifacts.

## Naming Guidelines

- Parent fodler (which are not Python packages) should be named in `kebab-case`.
- Python scripts and Python packages folders should be name in `snake_case`.
- TODO: Don't forget to change the PROJECT_NAME and REPO_NAME variables in following directories:
  - custom-pip-packages
  - pyproject.toml
  - setup.py

## Docstrings

Please use only the Google Style docstrings in your code. [Here](https://sphinxcontrib-napoleon.readthedocs.io/en/latest/example_google.html) is an example.

## Pre-Commits

To ensure code quality and maintain a clean repository, we use pre-commit hooks. You should set these up on your local machine.

### Local Development Environment Setup

We recommend using Poetry for managing dependencies.

#### Poetry

[Poetry](https://python-poetry.org/) is a Python dependency management tool that simplifies package management and project setup.

##### Installation

To install Poetry, open your terminal and run the following command:

```bash
pip install poetry
pip install toml-sort
```

##### Setting Up The Project

To set up the project with Poetry, navigate to the project directory and change the PROJECT_NAME in ´pyproject.toml´ and run the following commands:

```
# Resolve and install dependencies
poetry lock
poetry install

# Update all dependencies to their latest versions
poetry update
# Install important library
poetry add --dev 'black'
poetry add --dev tomli
poetry add tomli
```

These commands will ensure that your environment matches the project setup as defined in the pyproject.toml and poetry.lock files.

#### Pre-Commit configuration

We use pre-commit hooks to check and enforce code quality standards.

### Installation

To set up pre-commit hooks, first install the pre-commit package:

```bash
pip install pre-commit
pip install tomli
```

Then, set up the git hooks scripts:

```bash
pre-commit install
```

This will install the pre-commit script in your .git/hooks/ directory, which means the checks defined in .pre-commit-config.yaml will be run automatically every time you commit changes to your code.

Please make sure to update these setups regularly to incorporate any new changes in the project configuration.

### Problem hints for trying when pre-commits do cause problems

Use some of these commands:

```bash
pip install --upgrade pre-commit
pre-commit clean
rm -rf /~/.cache/pre-commit
pre-commit autoupdate
pre-commit install

#or manualy delete the cache directory like
rm -rf /var/folders/m0/d2g9969j35b350vns_9gww_r0000gn/T/*

# uninstall and reinstall
pip uninstall pre-commit
pip install pre-commit

# same using poetry
poetry remove pre-commit
poetry add pre-commit

# further attempts
rm -rf /~/.cache/pre-commit/repokmatndga/
```

### After updating .pre-commit-config.yaml

```bash
pre-commit run --all-files
pre-commit autoupdate
```
