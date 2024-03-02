# Custom Python Package

This Python package is part of the datadice and gaming-academy project and provides custom functionality tailored for it which is standardized.

## Installation

Use the package manager [pip](https://pip.pypa.io/en/stable/) to install this custom pip package.

Replace `3.x` with your specific Python version in the following command:

```bash
pip3.x install git+https://github.com/datadice-io/<PROJECT_NAME>.git#subdirectory=custom-pip-package
```

Note: The ".x" indicates the version of your python interpreter, otherwise the package will not be found

## Updating the pip package

When making changes to this package, ensure to increment the "version" number in the setup.py file. If this step is overlooked, your changes may not be reflected upon package update.

To update the package, use the same command as for the installation, pip will handle the update process:

```bash
pip3.9 install --upgrade git+https://github.com/datadice-io/<PROJECT_NAME>.git#subdirectory=custom-pip-package
```
