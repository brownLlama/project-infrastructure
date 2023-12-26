"""
This module provides utilities to interact with Google Firestore using paths.

Modules:
    firebase_admin
    google.cloud.firestore

Imports:
    os
    ..quickops_toolkit.logger

Classes:
    FirestorePathError: Exception for Firestore path-related errors.
    CloudFirestoreController: Controller to interact with Firestore.
"""

import json
import os

import firebase_admin
import google.cloud.firestore as firestore
from firebase_admin import credentials as fb_credentials
from firebase_admin import firestore as firebase_firestore
from google.cloud.firestore import Increment
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
    wait_fixed,
)

from ..quickops_toolkit.logger import get_logger

logger = get_logger(__name__)


DOCUMENT = "document"
COLLECTION = "collection"


class FirestorePathError(
    ValueError
):  # Inherit from ValueError or a more relevant base exception if preferred.
    """
    Exception raised for errors related to Firestore path handling.

    Attributes:
        path (list): input path which caused the error.
        message (str): explanation of the error.
    """

    def __init__(self, path: list, message: str = "Invalid Firestore path provided"):
        """
        Initialize FirestorePathError.

        Args:
            path (list): The path causing the error.
            message (str): Explanation of the error. Defaults to "Invalid Firestore path provided".
        """
        self.path = path
        self.message = f"{message}: {'/'.join(path)}"
        super().__init__(self.message)


class CloudFirestoreController:
    """
    A controller to interact with Firestore.

    Attributes:
        credentials_path (str): Path to Firebase credentials.
        firebase_client (firestore.Client): Firestore client instance.
    """

    def __init__(self, firebase_project_id: str, firebase_credentials_path: str = None):
        """
        Initialize the CloudFirestoreController.

        Args:
            firebase_project_id (str): The project ID for Firebase.
            firebase_credentials_path (str): Path to Firebase credentials. Defaults to None.
        """
        self.credentials_path = firebase_credentials_path or os.environ.get(
            "GOOGLE_APPLICATION_CREDENTIALS"
        )
        self.firebase_client = self.get_firebase_firestore_client(
            self.credentials_path, firebase_project_id
        )

    @staticmethod
    @retry(
        stop=stop_after_attempt(6),
        wait=wait_exponential(multiplier=1, min=2, max=300),
        retry=retry_if_exception_type(Exception),
    )
    def retryable_operation(func, *args, **kwargs):
        """
        Perform a retryable operation using the provided function.

        This function logs the retry attempt and then calls the passed
        function with the provided arguments and keyword arguments.

        Args:
            func (Callable): The function to retry.
            *args (Any): Variable-length argument list to pass to the function.
            **kwargs (Any): Arbitrary keyword arguments to pass to the function.

        Returns:
            The return value of the function call.
        """
        logger.debug(
            f"Retrying Firestore operation: {func.__name__} with args: {args} and kwargs: {kwargs}"
        )
        return func(*args, **kwargs)

    @staticmethod
    def get_firebase_firestore_client(
        credentials_path: str, project_id: str
    ) -> firestore.Client:
        """
        Retrieve or initializes and retrieves a Firestore client.

        Args:
            credentials_path (str): Path to Firebase credentials.
            project_id (str): The project ID for Firebase.

        Returns:
            firestore.Client: Firestore client instance.
        """
        if firebase_admin._apps:
            # If the default app already exists, return its client
            return firebase_firestore.client(firebase_admin.get_app())

        # If you reach here, it means the app isn't initialized, so you'll need to initialize it.
        app_params = {"projectId": project_id}

        if credentials_path:
            cred = fb_credentials.Certificate(credentials_path)
            app = firebase_admin.initialize_app(cred, app_params)
        else:
            app = firebase_admin.initialize_app(options=app_params)

        return firebase_firestore.client(app)

    def get_reference_by_path(self, path: list):
        """
        Retrieve a Firestore reference based on a given path.

        Args:
            path (list): The path to the Firestore reference.

        Returns:
            tuple: A tuple containing the type of the reference ("document" or "collection") and the reference itself.
        """
        ref = self.firebase_client
        is_collection = len(path) % 2 != 0

        if is_collection:
            ref_type = COLLECTION
        else:
            ref_type = DOCUMENT

        for idx, path_element in enumerate(path):
            if idx % 2 == 0:
                ref = ref.collection(path_element)
            else:
                ref = ref.document(path_element)

        return ref_type, ref

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_fixed(1),
        retry=retry_if_exception_type(Exception),
    )
    def set_by_path(self, path: list, data: dict):
        """
        Set data at a Firestore path.

        Args:
            path (list): The path to the Firestore document.
            data (dict): The data to set.

        Raises:
            FirestorePathError: If the path does not point to a document.
        """
        ref_type, doc_ref = self.get_reference_by_path(path)

        if ref_type == DOCUMENT:
            doc_ref.set(data)
        elif ref_type == COLLECTION:
            doc_ref.add(data)
        else:
            raise FirestorePathError(
                path, "Path must point to a document or a collection."
            )

    def batch_set_by_path(self, operations: list):
        """
        Perform a batch upsert operation for a list of documents.

        Args:
            operations (list): A list of tuples, where each tuple contains a path (list)
                               and data (dict) for the upsert operation.
                               Example: [(['path', 'to', 'doc1'], {'field1': 'value1'}), ...]

        Raises:
            FirestorePathError: If any path does not point to a document.
        """
        try:
            # Start a new batch
            batch = self.firebase_client.batch()

            for entry in operations:
                ref_type, doc_ref = self.get_reference_by_path(entry["full_reference"])

                if ref_type == DOCUMENT:
                    document_data = (
                        json.loads(entry["document_content"])
                        if isinstance(entry["document_content"], str)
                        else entry["document_content"]
                    )
                    batch.set(doc_ref, document_data, merge=False)  # Add to batch
                else:
                    raise FirestorePathError(
                        entry["full_reference"], "Path must point to a document."
                    )

            # Commit the batch
            batch.commit()
        except Exception as e:
            logger.error(f"Error performing batch upsert: {e}", exc_info=True)

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_fixed(1),
        retry=retry_if_exception_type(Exception),
    )
    def upsert_by_path(self, path: list, data: dict):
        """
        Update data at a Firestore path, creating the document if it doesn't exist.

        Args:
            path (list): The path to the Firestore document.
            data (dict): The data to update.

        Raises:
            FirestorePathError: If the path does not point to a document.
        """
        ref_type, doc_ref = self.get_reference_by_path(path)

        if ref_type == DOCUMENT:
            doc_ref.set(data, merge=True)  # Use the `merge` parameter
        else:
            raise FirestorePathError(path, "Path must point to a document.")

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_fixed(1),
        retry=retry_if_exception_type(Exception),
    )
    def batch_upsert_by_path(self, operations: list):
        """
        Perform a batch upsert operation for a list of documents.

        Args:
            operations (list): A list of tuples, where each tuple contains a path (list)
                               and data (dict) for the upsert operation.
                               Example: [(['path', 'to', 'doc1'], {'field1': 'value1'}), ...]

        Raises:
            FirestorePathError: If any path does not point to a document.
        """
        try:
            # Start a new batch
            batch = self.firebase_client.batch()

            for entry in operations:
                ref_type, doc_ref = self.get_reference_by_path(entry["full_reference"])

                if ref_type == DOCUMENT:
                    document_data = (
                        json.loads(entry["document_content"])
                        if isinstance(entry["document_content"], str)
                        else entry["document_content"]
                    )
                    batch.set(doc_ref, document_data, merge=True)  # Add to batch
                else:
                    raise FirestorePathError(
                        entry["full_reference"], "Path must point to a document."
                    )

            # Commit the batch
            batch.commit()
        except Exception as e:
            logger.error(f"Error performing batch upsert: {e}", exc_info=True)

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_fixed(1),
        retry=retry_if_exception_type(Exception),
    )
    def modify_counter_by_path(
        self, path: list, field_name: str, mode: str, increment_by: int = 1
    ):
        """
        Modify a numeric field in a document at a specified path by either incrementing it or resetting it to zero.

        Args:
            path (list): The path to the Firestore document.
            field_name (str): The field to be modified.
            mode (str): The operation mode - "increment" or "reset".
            increment_by (int): The amount to increment by. Defaults to 1.

        Raises:
            FirestorePathError: If the path does not point to a document or if an invalid mode is provided.
        """
        # Ensure the path points to a document
        if len(path) % 2 == 0:
            ref_type, doc_ref = self.get_reference_by_path(path)

            if ref_type != DOCUMENT:
                raise FirestorePathError(
                    path, "Path must point to a document to modify a counter."
                )

            if mode == "increment":
                doc_ref.update({field_name: Increment(increment_by)})
            elif mode == "reset":
                doc_ref.update({field_name: 0})
            else:
                raise ValueError("Invalid mode provided. Use 'increment' or 'reset'.")
        else:
            raise FirestorePathError(
                path, "Path provided points to a collection, expected a document path."
            )

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_fixed(1),
        retry=retry_if_exception_type(Exception),
    )
    def update_by_path(self, path: list, data: dict):
        """
        Update data at a Firestore path.

        Args:
            path (list): The path to the Firestore document.
            data (dict): The data to update.

        Raises:
            FirestorePathError: If the path does not point to a document.
        """
        ref_type, doc_ref = self.get_reference_by_path(path)

        if ref_type == DOCUMENT:
            doc_ref.update(data)
        else:
            raise FirestorePathError(path, "Path must point to a document.")

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_fixed(1),
        retry=retry_if_exception_type(Exception),
    )
    def get_by_path(self, path: list):
        """
        Retrieve data from a Firestore path.

        Args:
            path (list): The path to the Firestore reference.

        Returns:
            dict or list or None: Data from Firestore or None if not exists.
        """
        ref_type, ref = self.get_reference_by_path(path)
        if ref_type == COLLECTION:
            return [doc.to_dict() for doc in ref.stream()]
        elif ref_type == DOCUMENT:
            doc = ref.get()
            if doc.exists:
                return doc.to_dict()
        return None

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_fixed(1),
        retry=retry_if_exception_type(Exception),
    )
    def delete_by_path(self, path: list):
        """
        Delete data or a collection from a Firestore path.

        Args:
            path (list): The path to the Firestore reference.
        """
        ref_type, ref = self.get_reference_by_path(path)
        if ref_type == DOCUMENT:
            ref.delete()
        elif ref_type == COLLECTION:
            for doc in ref.stream():
                doc.reference.delete()

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_fixed(1),
        retry=retry_if_exception_type(Exception),
    )
    def exists_by_path(self, path: list) -> bool:
        """
        Check if a document or collection exists at a Firestore path.

        Args:
            path (list): The path to the Firestore reference.

        Returns:
            bool: True if the reference exists, otherwise False.
        """
        ref_type, ref = self.get_reference_by_path(path)
        if ref_type == DOCUMENT:
            return ref.get().exists
        elif ref_type == COLLECTION:
            try:
                # Check if the collection has any documents
                doc = next(iter(ref.limit(1).stream()), None)
                if doc:
                    return True
                else:
                    return False
            except Exception as e:
                logger.error(f"Error checking if collection exists: {e}", exc_info=True)
                return False

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_fixed(1),
        retry=retry_if_exception_type(Exception),
    )
    def query_collection_by_path(
        self,
        path: list,
        query_params: list = None,
        sort_by=None,
        limit=None,
        start_after=None,
    ):
        """
        Query documents within a collection.

        It is based on provided query parameters and includes the document ID in the results.

        Args:
            path (list): The path to the Firestore collection.
            query_params (list): List of tuples with query parameters, where each tuple
                has a field, operator, and value. Defaults to None, which fetches all documents.
            sort_by (tuple, optional): Tuple containing the field name to sort by and the direction
                (either 'ASC' for ascending or 'DESC' for descending). E.g., ('timestamp', 'DESC').
            limit (int, optional): The maximum number of results to return.
            start_after (dict, optional): The document to start after. This is useful for paginating
                results. Start after the document you want to start after and provide the limit. Defaults to None.

        Returns:
            list: List of documents matching the query, each including its document ID.

        Raises:
            FirestorePathError: If the path does not point to a collection.
        """
        ref_type, collection_ref = self.get_reference_by_path(path)

        if ref_type != COLLECTION:
            raise FirestorePathError(path, "Path must point to a collection.")

        query = collection_ref
        if query_params:
            for field, operator, value in query_params:
                query = query.where(field, operator, value)

        # Sort if sort_by is provided
        if sort_by:
            field_name, direction = sort_by
            if direction == "ASC":
                query = query.order_by(field_name, direction=firestore.Query.ASCENDING)
            elif direction == "DESC":
                query = query.order_by(field_name, direction=firestore.Query.DESCENDING)
            else:
                raise ValueError("Sort direction should be 'ASC' or 'DESC'")

        # Pagination logic
        if start_after:
            query = query.start_after(start_after)

        # Limit if limit is provided
        if limit:
            query = query.limit(limit)

        # Get the documents and add the document ID to the result
        results = []
        for doc in query.stream():
            doc_dict = doc.to_dict()
            doc_dict["documentId"] = doc.id  # Add the document ID to the dictionary
            results.append(doc_dict)

        return results
