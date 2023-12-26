"""
This module provides controllers and operations for various Google Cloud Platform (GCP) services.

It includes controllers for BigQuery, Cloud Firestore, Cloud Tasks, and GCP Secrets, as well as operations for BigQuery.
Each controller and operations class is designed to facilitate interaction with its respective GCP service,
allowing for streamlined and efficient management of cloud resources. The module is structured to allow easy
creation and configuration of these controllers with project-specific settings.

Functions:
    get_bigquery_controller(project_id: str) -> BigQueryController
    get_bigquery_operations(root_path: str = None) -> BQOperations
    get_cloud_firestore_controller(project_id: str) -> CloudFirestoreController
    get_gcp_secret_controller(project_id: str) -> GCPSecretController
    get_cloud_tasks_controller(project_id: str) -> CloudTasksController
"""

from ..gcp_toolkit.bigquery_controller import BigQueryController
from ..gcp_toolkit.bigquery_operations import BQOperations
from ..gcp_toolkit.cloud_firestore_controller import CloudFirestoreController
from ..gcp_toolkit.cloud_tasks_controller import CloudTasksController
from ..gcp_toolkit.secret_controller import GCPSecretController


def get_bigquery_controller(project_id: str):
    """
    Get BigQuery Controller Object.

    This function creates and returns a BigQueryController object configured
    with the project ID, dataset name, and table name from the provided config.

    Returns:
        BigQueryController: A BigQueryController object.
    """
    return BigQueryController(
        project_id=project_id,
    )


def get_bigquery_operations(root_path: str = None):
    """
    Get BigQuery Operations Object.

    This function creates and returns a BQOperations object.

    Returns:
        BQOperations: A BQOperations object.
    """
    return BQOperations(root_path=root_path)


def get_cloud_firestore_controller(project_id: str):
    """
    Get CloudFirestoreController Object.

    This function creates and returns a CloudFirestoreController object configured
    with the project ID, dataset name, and table name specified in endpoint_configs.

    Returns:
        CloudFirestoreController: A CloudFirestoreController object.
    """
    return CloudFirestoreController(
        firebase_project_id=project_id,
    )


def get_gcp_secret_controller(project_id: str):
    """
    Get GCPSecretController Object.

    This function creates and returns a GCPSecretController object configured
    with the project ID, dataset name, and table name specified in endpoint_configs.

    Returns:
        GCPSecretController: A GCPSecretController object.
    """
    return GCPSecretController(
        project_id=project_id,
    )


def get_cloud_tasks_controller(project_id: str):
    """
    Get CloudTasksController Object.

    This function creates and returns a CloudTasksController object configured
    with the project ID, dataset name, and table name specified in endpoint_configs.

    Returns:
        CloudTasksController: A CloudTasksController object.
    """
    return CloudTasksController(
        project_id=project_id,
    )
