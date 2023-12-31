"""
This module provides classes for handling BigQuery operations.

This includes a main class `BQOperations` for handling standard operations on BigQuery,
and minimizing code duplication. `BQOperations` includes methods for fetching the latest
value of a specified column from a BigQuery table, importing raw data into a BigQuery table,
preparing data for BigQuery, handling exceptions, and loading schemas.
"""

import traceback
from typing import Any, Dict, List, Optional, Tuple, Union

from google.cloud import bigquery

from ..quickops_toolkit.logger import get_logger
from .bigquery_jobs import BigQueryJobs

# initialize logger
logger = get_logger(__name__)


class BQOperations:
    """Handle standard BigQuery operations."""

    def __init__(
        self,
        root_path: str = None,
        service_account_info: Optional[Dict[str, Any]] = None,
    ):
        """
        Initialize the BQOperations instance.

        Args:
            root_path (str): The path of the root folder as string (like for example "/usr/app")
            service_account_info (Optional[Dict[str, Any]]): Service account information for BigQuery authentication.
        """
        self.root_path = root_path

        if service_account_info:
            self.__bq_jobs = BigQueryJobs(service_account_info=service_account_info)
        else:
            self.__bq_jobs = BigQueryJobs()

        self.bigquery_client = bigquery.Client()

    def get_table_schema_from_bigquery(self, dataset_id: str, table_id: str):
        """
        Fetch the schema of a specified table from BigQuery.

        Args:
            dataset_id (str): The ID of the dataset containing the table.
            table_id (str): The ID of the table to fetch the schema for.

        Returns:
            List[bigquery.SchemaField]: The schema of the table.
        """
        try:
            table_ref = self.bigquery_client.dataset(dataset_id).table(table_id)
            table = self.bigquery_client.get_table(table_ref)
            return table.schema
        except Exception as e:
            self._handle_exception(
                e,
                operation="get_table_schema_from_bigquery",
                dataset_id=dataset_id,
                table_id=table_id,
            )
            return None

    def retrieve_latest_value(
        self,
        dataset_id: str,
        table_id: str,
        column_name: str,
        default_value: Union[str, int],
    ) -> Union[str, int]:
        """
        Retrieve the latest value of a specified column from a BigQuery table.

        Args:
            dataset_id (str): Name of the dataset containing the target table.
            table_id (str): Name of the target table.
            column_name (str): Name of the column to retrieve the latest value from.
            default_value (Union[str, int]): Default value to return if no records are found.

        Returns:
            Union[str, int]: Latest value of the specified column or the default value if no records are found.
        """
        query = f"SELECT {column_name} FROM `{dataset_id}.{table_id}` ORDER BY {column_name} DESC LIMIT 1"

        try:
            query_job = self.bigquery_client.query(query)
            result = query_job.result()

            latest_value = next(iter(result), None)

            return getattr(latest_value, column_name, default_value)
        except Exception as e:
            self._handle_exception(
                e,
                operation="retrieve_latest_value",
                action="None",
                dataset_id=dataset_id,
                table_id=table_id,
            )

            return default_value

    def bq_import(
        self,
        raw_data: List[Dict[str, Any]],
        table_id: str,
        dataset_id: str,
        location: str,
        schema_path: str = None,
        ignore_unknown_values: bool = True,
        add_record_ts: bool = True,
        record_ts_field_name: str = "inserted_at",
        time_partitioning_field: str = None,
    ) -> None:
        """
        Import raw data into a BigQuery table.

        Args:
            raw_data (List[Dict[str, Any]]): List of dictionaries containing the data to be imported.
            table_id (str): Name of the BigQuery table to import data into.
            dataset_id (str): Name of the BigQuery dataset containing the target table.
            location (str): Geographic location of the BigQuery dataset.
            schema_path (str): Path of a table schema.
            ignore_unknown_values (bool): Whether to accept rows that contain values that do not match the schema.
            add_record_ts (bool): Whether to add a record timestamp to the data. Default True.
            record_ts_field_name (str): Name of the record timestamp field. Default "inserted_at".
            time_partitioning_field (str): Name of the field to partition the table by. Default None.
        """
        if not raw_data:
            logger.warning(
                f"No data found for table '{table_id}' in dataset '{dataset_id}'. Will continue"
            )
            return

        endpoint_schema, auto_detect = self._load_schema(
            dataset_id=dataset_id, table_id=table_id, schema_path=schema_path
        )

        self._prepare_data_list_for_bq(raw_data=raw_data)

        self.__bq_jobs.batch_import_json_to_bq(
            data=raw_data,
            dataset_id=dataset_id,
            location=location,
            table_id=table_id,
            ignore_unknown_values=ignore_unknown_values,
            autodetect_schema=auto_detect,
            table_schema=endpoint_schema if not auto_detect else None,
            add_record_ts=add_record_ts,
            record_ts_field_name=record_ts_field_name,
            time_partitioning_field=time_partitioning_field,
        )

    def _prepare_data_list_for_bq(self, raw_data: List[Dict[str, Any]]) -> None:
        """
        Prepare a list of dictionaries for BigQuery import.

        Recursively calls _prepare_data_dict_for_bq to replace empty dictionaries with None.

        Args:
            raw_data (List[Dict[str, Any]]): List of dictionaries to be prepared for BigQuery import.
        """
        for entry in raw_data:
            self._prepare_data_dict_for_bq(entry=entry)

    def _prepare_data_dict_for_bq(self, entry: Dict[str, Any]) -> None:
        """
        Prepare a dictionary for BigQuery import.

        Replaces empty dictionaries with None recursively.

        Args:
            entry (Dict[str, Any]): Dictionary to be prepared for BigQuery import.
        """
        if isinstance(entry, dict):
            for key, value in entry.items():
                if isinstance(value, list):
                    self._prepare_data_list_for_bq(value)
                elif isinstance(value, dict):
                    if not value:
                        entry[key] = None
                    else:
                        self._prepare_data_dict_for_bq(value)

    @staticmethod
    def _handle_exception(
        exception: Exception,
        operation: str,
        action: str = "None",
        **kwargs: Dict[str, Any],
    ) -> None:
        """
        Log the exception details with information about the operation and parameters.

        Args:
            exception (Exception): The exception to handle.
            operation (str): The name of the operation being performed.
            action (str): An expression of what is going to happen. Default "None"
            kwargs (Dict[str, Any]): Additional details about the operation.
        """
        logger.warning(
            f"\n{'=' * 10}\n"
            f"An exception occurred during operation {operation} with parameters {kwargs}\n"
            f"Catched Error: {exception}\n"
            f"Traceback: {traceback.format_exc()}\n"
            f"Action: {action}\n"
            f"{'=' * 10}\n"
        )

    def _load_schema(
        self, dataset_id: str, table_id: str, schema_path: Optional[str] = None
    ) -> Tuple[Optional[Any], bool]:
        """
        Load schema for a given table.

        Args:
            dataset_id (str): The ID of the dataset containing the table.
            table_id (str): The ID of the table to load schema for.
            schema_path (Optional[str]): Path of a table schema file.

        Returns:
            Tuple[Optional[Any], bool]: Tuple containing the loaded schema and a boolean indicating
                                        whether BigQuery autodetect is used.
        """
        if schema_path:
            try:
                return (
                    self.__bq_jobs.client_bigquery.schema_from_json(schema_path),
                    False,
                )
            except Exception as e:
                self._handle_exception(
                    e,
                    operation="_load_schema",
                    action="will continue with BQ auto-detect",
                    table_id=table_id,
                )
                return None, True
        else:
            schema = self.get_table_schema_from_bigquery(dataset_id, table_id)
            return schema, schema is None
