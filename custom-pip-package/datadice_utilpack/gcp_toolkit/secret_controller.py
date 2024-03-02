"""This module provides a class for managing operations related to Google Cloud Platform (GCP) Secret Manager."""

from typing import List, Optional

from google.cloud import secretmanager

from ..quickops_toolkit.logger import get_logger

# initialize logger
logger = get_logger(__name__)


class GCPSecretController:
    """Perform operations related to Google Cloud Platform (GCP) Secret Manager."""

    def __init__(self, project_id: Optional[str] = None) -> None:
        """Initialize an instance of GCPSecretManager.

        Args:
            project_id (str, optional): The GCP project id. Defaults to None.

        Raises:
            SystemExit: If project_id is not provided.
        """
        if project_id is None:
            logger.error("Please define a project_id")
            raise SystemExit(-1)
        self.client = secretmanager.SecretManagerServiceClient()
        self.project_id = project_id

    def create_secret(self, secret_id: str) -> None:
        """Create a new secret.

        Args:
            secret_id (str): The id of the secret to be created.
        """
        parent = f"projects/{self.project_id}"
        self.client.create_secret(
            request={
                "parent": parent,
                "secret_id": secret_id,
                "secret": {"replication": {"automatic": {}}},
            }
        )

    def add_secret_version(self, secret_id: str, secret_value: str) -> None:
        """Add a new secret version.

        Args:
            secret_id (str): The id of the secret to add a version to.
            secret_value (str): The value of the new secret version.
        """
        parent = self.client.secret_path(self.project_id, secret_id)
        payload = secret_value.encode("UTF-8")
        self.client.add_secret_version(
            request={"parent": parent, "payload": {"data": payload}}
        )

    def get_secret_value(self, secret_id: str, version_id: str = "latest") -> str:
        """Get the payload for the given secret version.

        Args:
            secret_id (str): The id of the secret to fetch the value from.
            version_id (str): The version of the secret to fetch. Defaults to "latest".

        Returns:
            str: The value of the requested secret version.
        """
        name = f"projects/{self.project_id}/secrets/{secret_id}/versions/{version_id}"
        response = self.client.access_secret_version(request={"name": name})
        return response.payload.data.decode("UTF-8")

    def list_secrets(self) -> List[secretmanager.Secret]:
        """List all secrets.

        Returns:
            List[secretmanager.Secret]: A list of all secrets.
        """
        parent = f"projects/{self.project_id}"
        return list(self.client.list_secrets(request={"parent": parent}))

    def list_secret_names(self) -> List[str]:
        """List names of all secrets.

        Returns:
            List[str]: A list of all secret names.
        """
        parent = f"projects/{self.project_id}"
        secret_name_list = [
            secret.name.split("/")[-1]
            for secret in self.client.list_secrets(request={"parent": parent})
        ]
        return secret_name_list

    def list_secret_versions(self, secret_id: str) -> List[secretmanager.SecretVersion]:
        """List all secret versions for a given secret.

        Args:
            secret_id (str): The id of the secret to list versions from.

        Returns:
            List[secretmanager.SecretVersion]: A list of all versions of the given secret.
        """
        parent = self.client.secret_path(self.project_id, secret_id)
        return list(self.client.list_secret_versions(request={"parent": parent}))

    def list_secret_version_names(self, secret_id: str) -> List[str]:
        """List names of all secret versions for a given secret.

        Args:
            secret_id (str): The id of the secret to list version names from.

        Returns:
            List[str]: A list of all version names of the given secret.
        """
        parent = self.client.secret_path(self.project_id, secret_id)
        version_name_list = [
            version.name.split("/")[-1]
            for version in self.client.list_secret_versions(request={"parent": parent})
        ]
        return version_name_list
