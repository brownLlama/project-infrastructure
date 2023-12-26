"""
Setup script for the utilkit package.

This script uses setuptools to package the utilkit module, providing metadata and
install requirements, so it can be easily installed and distributed.
"""
from setuptools import find_packages, setup

setup(
    name="PROJECT_NAME_utilpack",
    version="1.99",
    packages=find_packages(where="."),
    author="datadice-io",
    author_email="it@datadice.io",
    description="This package is to be used for standardized scripts",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/REPO_NAME/PROJECT_NAME",
    install_requires=[
        "requests==2.31.0",
        "google-cloud-secret-manager==2.16.1",
        "google-cloud-bigquery==3.11.2",
        "google-cloud-storage==2.9.0",
        "google-auth==2.20.0",
        "google-cloud-tasks==2.14.2",
        "google-cloud-monitoring==2.15.1",
        "firebase-admin==6.2.0",
        "google-cloud-firestore==2.12.0",
        "tenacity==8.2.3",
    ],
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
    ],
)
