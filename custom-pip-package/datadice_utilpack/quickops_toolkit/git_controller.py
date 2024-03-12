"""Module for managing Git operations with support for GCP secrets."""

import os
import shutil
import tempfile

from git import GitCommandError, Repo

from ..gcp_toolkit.secret_controller import GCPSecretController
from .logger import get_logger

logger = get_logger(__name__)


class _SSHKeyContextManager:
    """Context manager for handling temporary SSH keys."""

    def __init__(self, ssh_key_file, original_ssh_agent):
        self.ssh_key_file = ssh_key_file
        self.original_ssh_agent = original_ssh_agent

    def __enter__(self):
        pass

    def __exit__(self, exc_type, exc_val, exc_tb):
        os.unlink(self.ssh_key_file)
        if self.original_ssh_agent:
            os.environ["SSH_AUTH_SOCK"] = self.original_ssh_agent
        else:
            del os.environ["SSH_AUTH_SOCK"]


class GitController:
    """Manages Git operations using GCP secrets for authentication."""

    def __init__(self, project_id):
        """
        Initialize the GitController with a specific GCP project ID.

        Args:
            project_id (str): The GCP project ID.
        """
        self.secret_controller = GCPSecretController(project_id)

    def clone_repo(self, ssh_url, ssh_key_secret_id, target_dir, branch="main"):
        """
        Clone a repository using SSH authentication.

        This method clones the repository at the specified SSH URL into the target directory,
        using the SSH key retrieved from a GCP secret.

        Args:
            ssh_url (str): The SSH URL of the repository.
            ssh_key_secret_id (str): The ID of the GCP secret containing the SSH key.
            target_dir (str): The directory where the repository will be cloned.
            branch (str, optional): The branch to clone (default is "main").
        """
        try:
            self._clear_directory(target_dir)
            self._setup_ssh_key(ssh_key_secret_id)
            Repo.clone_from(ssh_url, target_dir, branch=branch)
            logger.info(
                f"Repository successfully cloned to {target_dir} on branch {branch}"
            )
        except GitCommandError as e:
            logger.error(f"Error cloning repository: {e}")

    @staticmethod
    def _clear_directory(path):
        """
        Clear the specified directory.

        Args:
            path (str): The path to the directory to clear.
        """
        if os.path.exists(path):
            shutil.rmtree(path)

    def _setup_ssh_key(self, ssh_key_secret_id):
        """
        Set up SSH key for Git operations.

        Args:
            ssh_key_secret_id (str): The ID of the GCP secret containing the SSH key.

        Returns:
            _SSHKeyContextManager: A context manager for handling temporary SSH keys.
        """
        ssh_key = self.secret_controller.get_secret_value(ssh_key_secret_id)
        ssh_key_file = tempfile.NamedTemporaryFile(delete=False)
        ssh_key_file.write(ssh_key.encode())
        ssh_key_file.close()
        os.chmod(ssh_key_file.name, 0o400)

        original_ssh_agent = os.environ.get("SSH_AUTH_SOCK", None)
        os.environ["SSH_AUTH_SOCK"] = ""  # Disable any existing SSH agent
        os.environ["GIT_SSH_COMMAND"] = (
            f"ssh "
            f"-i {ssh_key_file.name} "
            f"-o IdentitiesOnly=yes "
            f"-o UserKnownHostsFile=/dev/null "
            f"-o StrictHostKeyChecking=no"
        )

        return _SSHKeyContextManager(ssh_key_file.name, original_ssh_agent)
