"""
Controller for BigQuery Operations.

This script contains a class, BigQueryController, that wraps around the Google BigQuery
client library to provide higher-level functions for manipulating BigQuery tables. It includes
methods for upserting rows, deleting rows, and selecting rows based on conditions. The script also
includes custom exception handling and logging.

Note:
    This script depends on the `google.cloud.bigquery` library.

Example:
    To use this script, initialize the BigQueryController class and then call its methods:

        controller = BigQueryController("my_project_id", "my_dataset_name", "my_table_name")
        controller.upsert_rows(rows_to_insert, "id")
"""

import json
import uuid
from io import BytesIO
from pathlib import Path
from time import sleep
from typing import List, Tuple

from google.cloud import bigquery
from google.cloud.exceptions import NotFound

from ..quickops_toolkit.custom_error import (  # DeleteRequestError,
    GetRequestError,
    UpsertRequestError,
)
from ..quickops_toolkit.logger import get_logger

logger = get_logger(__name__)


class BigQueryController:
    """
    Handle operations on a BigQuery table.

    Attributes:
        project_id (str): The project ID in GCP.
        client (bigquery.Client): Client to interact with the BigQuery service.
    """

    def __init__(self, project_id: str):
        """
        Initialize the BigQueryController with project, dataset, and table information.

        Args:
            project_id (str): The project ID in GCP.
        """
        self.project_id = project_id
        self.client = bigquery.Client(project=project_id)

    def _get_table_reference(self, dataset_id: str, table_id: str):
        """Get the full table reference in the format 'project.dataset.table'.

        Returns:
            str: The full table reference.
        """
        return f"{self.project_id}.{dataset_id}.{table_id}"

    def _create_temp_table(self, full_temp_table_ref, dataset_id: str, table_id: str):
        logger.debug(f"Attempting to create temporary table {full_temp_table_ref}")
        main_table = self.client.get_table(
            self._get_table_reference(dataset_id=dataset_id, table_id=table_id)
        )
        temp_table = bigquery.Table(full_temp_table_ref, schema=main_table.schema)
        self.client.create_table(temp_table)

        # Adding verification attempts
        verification_attempts = 2
        delay_seconds = 3  # Time delay in seconds between each verification attempt

        for i in range(verification_attempts):
            sleep(delay_seconds)
            try:
                self.client.get_table(full_temp_table_ref)
                logger.debug(f"Verified the table {full_temp_table_ref} exists.")
                return  # Table exists, exit the function
            except Exception as e:
                logger.warning(
                    f"Attempt {i + 1}: Failed to verify the table {full_temp_table_ref}. Trying again. Error: {e}"
                )

        # If control reaches here, verification failed
        logger.error(
            f"Failed to verify the table {full_temp_table_ref} after {verification_attempts} attempts."
        )
        raise Exception(
            f"Could not verify the existence of table {full_temp_table_ref}"
        )

    def _load_schema(self, path: str) -> Tuple[List[bigquery.SchemaField], bool]:
        """
        Load schema for a given table.

        Returns a tuple containing the schema and a boolean indicating whether
        BigQuery autodetect is used.

        Args:
            path (str): The path to the schema file

        Returns:
            Tuple[List[bigquery.SchemaField], bool]: the loaded schema and autodetect flag

        Raises:
            Exception: If the schema could not be loaded.
        """
        try:
            return self.client.schema_from_json(Path(f"{path}")), False
        except Exception as e:
            logger.error(f"An error occurred while loading schema: {e}", exc_info=True)
            raise Exception(f"Could not load schema from {path}")

    def _insert_into_temp_table(
        self,
        temp_table,
        rows_to_insert,
        max_retries=5,
        location="EU",
        schema_path=None,
        ignore_unknown_values=True,
    ):
        logger.debug(f"Parsed temp table: {temp_table}")

        job_config = bigquery.LoadJobConfig()
        job_config.source_format = bigquery.SourceFormat.NEWLINE_DELIMITED_JSON
        job_config.write_disposition = bigquery.WriteDisposition.WRITE_APPEND
        job_config.ignore_unknown_values = ignore_unknown_values
        if schema_path:
            table_schema, autodetect = self._load_schema(schema_path)
            job_config.schema = table_schema
            job_config.autodetect = autodetect
        else:
            job_config.autodetect = (
                True  # Enable auto-detection if no schema path is provided
            )

        for attempt in range(max_retries):
            try:
                results_newline_json = "\n".join(
                    [json.dumps(row) for row in rows_to_insert]
                )
                byte_file = BytesIO(results_newline_json.encode())
                byte_file.seek(0)

                self.client.load_table_from_file(
                    file_obj=byte_file,
                    destination=temp_table,
                    location=location,
                    job_config=job_config,
                ).result()

                return  # Insert successful, exit function

            except Exception as e:
                logger.error(f"Insert attempt {attempt + 1} failed: {e}")

            sleep(2**attempt)  # Exponential back-off

        logger.error(
            f"Failed to insert rows into {temp_table} after {max_retries} attempts."
        )
        raise Exception(f"Could not insert rows into {temp_table}")

    def _fetch_and_compare_schemas(self, main_table_ref, temp_table_ref):
        """
        Fetch and compares the schemas of the main and temporary tables.

        Args:
            main_table_ref (str): The full reference to the main table.
            temp_table_ref (str): The full reference to the temporary table.

        Raises:
            ValueError: If the schemas don't match.
        """
        main_table = self.client.get_table(main_table_ref)
        temp_table = self.client.get_table(temp_table_ref)

        if main_table.schema != temp_table.schema:
            logger.error(
                "Schemas of main table and temporary table do not match. Aborting."
            )
            raise ValueError("Mismatched table schemas")

    def _generate_sql_merge(self, main_table_ref, temp_table_ref, unique_columns):
        """
        Generate an SQL MERGE query to upsert rows.

        Args:
            main_table_ref (str): The full reference to the main table.
            temp_table_ref (str): The full reference to the temporary table.
            unique_columns (list[str]): The list of unique columns used to match rows.

        Returns:
            str: The SQL MERGE query.
        """
        main_table = self.client.get_table(main_table_ref)
        columns_to_update = [field.name for field in main_table.schema]

        update_set_statements = ", ".join(
            [f"T.{col} = S.{col}" for col in columns_to_update]
        )
        insert_columns = ", ".join(columns_to_update)
        insert_values = ", ".join([f"S.{col}" for col in columns_to_update])

        on_conditions = " AND ".join([f"T.{col} = S.{col}" for col in unique_columns])

        return f"""
        MERGE `{main_table_ref}` T
        USING `{temp_table_ref}` S
        ON {on_conditions}
        WHEN MATCHED THEN
            UPDATE SET {update_set_statements}
        WHEN NOT MATCHED THEN
            INSERT ({insert_columns})
            VALUES({insert_values})
        """

    def _table_exists(self, dataset_id: str, table_id: str) -> bool:
        """
        Check if a table exists in the dataset.

        Args:
            dataset_id (str): The dataset ID within the project.
            table_id (str): The table ID within the dataset.

        Returns:
            bool: True if the table exists, otherwise False.
        """
        table_ref = self.client.dataset(dataset_id).table(table_id)
        try:
            self.client.get_table(table_ref)
            return True
        except NotFound:
            return False

    def _create_new_table(self, dataset_id: str, table_id: str, schema_path: str):
        """
        Create a new table with the given schema.

        Args:
            dataset_id (str): The dataset ID within the project.
            table_id (str): The table ID within the dataset.
            schema_path (str): The path to the schema file.
        """
        schema, _ = self._load_schema(schema_path)
        table_ref = self.client.dataset(dataset_id).table(table_id)
        table = bigquery.Table(table_ref, schema=schema)
        self.client.create_table(table)

    def upsert_rows(
        self,
        dataset_id,
        table_id,
        rows_to_insert,
        unique_columns,
        schema_path=None,
        ignore_unknown_values=True,
    ):
        """
        Upsert rows into the BigQuery table.

        Args:
            dataset_id (str): The dataset ID within the project.
            table_id (str): The table ID within the dataset.
            rows_to_insert (list): The rows to upsert.
            unique_columns (list[str]): The list of unique columns used to match rows.
            schema_path (str): path string where the schema of the table lives

        Raises:
            UpsertRequestError: If upsert operation fails.
        """
        if not self._table_exists(dataset_id, table_id):
            logger.info(
                f"Table {table_id} does not exist. Creating it with provided schema."
            )
            if not schema_path:
                raise ValueError("Schema path must be provided to create a new table.")
            self._create_new_table(dataset_id, table_id, schema_path)

        full_temp_table_ref = (
            f"{self._get_table_reference(dataset_id=dataset_id, table_id=table_id)}"
            f"_temp_{str(uuid.uuid4()).replace('-', '')}"
        )
        try:
            # Create and populate the temporary table
            self._create_temp_table(
                full_temp_table_ref=full_temp_table_ref,
                dataset_id=dataset_id,
                table_id=table_id,
            )
            temp_table = self.client.get_table(full_temp_table_ref)
            self._insert_into_temp_table(
                temp_table,
                rows_to_insert,
                schema_path=schema_path,
                ignore_unknown_values=ignore_unknown_values,
            )

            # Fetch and compare the schemas
            self._fetch_and_compare_schemas(
                self._get_table_reference(dataset_id=dataset_id, table_id=table_id),
                full_temp_table_ref,
            )

            # Generate and run the SQL merge query
            sql_merge = self._generate_sql_merge(
                self._get_table_reference(dataset_id=dataset_id, table_id=table_id),
                full_temp_table_ref,
                unique_columns,
            )
            query_job = self.client.query(sql_merge)
            query_job.result()

            logger.info("Rows successfully upserted.")
        except Exception as e:
            logger.error(f"An error occurred upserting: {e}", exc_info=True)
            raise UpsertRequestError(418, f"Code 418: Upsert failed - {e}")
        finally:
            self.client.delete_table(full_temp_table_ref)

    def select_rows(self, dataset_id, table_id, columns_to_select, condition):
        """
        Select rows from the BigQuery table based on a condition.

        Args:
            columns_to_select (list[str]): The columns to select.
            condition (str): The SQL condition for selecting rows.
            dataset_id (str): The dataset ID within the project.
            table_id (str): The table ID within the dataset.

        Returns:
            list: A list of rows that match the condition.

        Raises:
            GetRequestError: If select operation fails.
        """
        try:
            query = (
                f"SELECT {', '.join(columns_to_select)} "
                f"FROM `{self._get_table_reference(dataset_id=dataset_id, table_id=table_id)}` "
                f"WHERE {condition}"
            )
            query_job = self.client.query(query)
            results = query_job.result()
            rows = [dict(row) for row in results]
            return rows
        except Exception as e:
            logger.error(f"An error occurred while selecting rows: {e}", exc_info=True)
            raise GetRequestError(406, f"Code 406: Select failed - {e}")

    def select_rows_paginated(self, dataset_id, table_id, limit=100, offset=0):
        """
        Select rows from the BigQuery table based on a condition with pagination.

        Args:
            limit (int): The maximum number of rows to return.
            offset (int): The starting index to return rows.
            dataset_id (str): The dataset ID within the project.
            table_id (str): The table ID within the dataset.

        Returns:
            list: A list of rows that match the condition.
            str: A message if no rows are returned.

        Raises:
            GetRequestError: If select operation fails.
        """
        try:
            query = (
                f"SELECT * FROM `{self._get_table_reference(dataset_id=dataset_id, table_id=table_id)}` "
                f"LIMIT {limit} OFFSET {offset}"
            )
            query_job = self.client.query(query)
            results = query_job.result()
            rows = [dict(row) for row in results]

            if not rows:
                return []

            return rows
        except Exception as e:
            logger.error(f"An error occurred while selecting rows: {e}", exc_info=True)
            raise GetRequestError(406, f"Code 406: Select failed - {e}")
