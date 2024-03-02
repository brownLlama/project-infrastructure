"""
Setup script for the utilkit package.

This script uses setuptools to package the utilkit module, providing metadata and
install requirements, so it can be easily installed and distributed.
"""

from setuptools import find_packages, setup

setup(
    name="datadice_utilpack",
    version="2.4.1",
    packages=find_packages(where="."),
    author="datadice-io",
    author_email="it@datadice.io",
    description="This package is to be used for standardized scripts",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/datadice-io/datadice",
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
        "psycopg2-binary==2.9.9",
        "GitPython==3.1.40",
        "google-cloud-pubsub==2.19.0",
        "pytz==2024.1",
    ],
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
    ],
)
