"""This module contains the BigQueryJobs class for handling operations related to BigQuery."""

import datetime
import json
import os
from io import BytesIO
from typing import Any, Dict, List, Optional, Union

from google.cloud import bigquery, storage
from google.oauth2 import service_account


class BigQueryJobs:
    """
    Handles operations related to BigQuery.

    This includes loading and querying data, and creating, deleting, and exporting tables.

    Attributes:
        client_bigquery: An instance of the BigQuery client.
        client_storage: An instance of the Cloud Storage client.
    """

    def __init__(self, service_account_info: Optional[Dict[str, str]] = None) -> None:
        """
        Initialize the BigQueryJobs with provided service account info.

        Args:
            service_account_info (Optional[Dict[str, str]]): The service account information. Defaults to None.
        """
        credentials = (
            service_account.Credentials.from_service_account_info(service_account_info)
            if service_account_info
            else None
        )
        self.client_bigquery = bigquery.Client(credentials=credentials)
        self.client_storage = storage.Client(credentials=credentials)

    def create_bq_table(
        self,
        dataset_id: str,
        table_id: str,
        schema_path: str,
        time_partitioning_field: Optional[str] = None,
        clustering_fields: Optional[List[str]] = None,
    ) -> None:
        """Create a new BigQuery table.

        Args:
            dataset_id (str): The name of the dataset.
            table_id (str): The name of the table.
            schema_path (str): The path to the JSON schema file.
            time_partitioning_field (Optional[str]): The name of the field used for time partitioning. Defaults to None.
            clustering_fields (Optional[List[str]]): A list of fields to use for clustering. Defaults to None.
        """
        table_ref = self.client_bigquery.dataset(dataset_id).table(table_id)

        if not self.client_bigquery.get_table(table_ref, retry=bigquery.DEFAULT_RETRY):
            table = bigquery.Table(
                table_ref, schema=self._parse_bq_json_schema(schema_path)
            )

            if time_partitioning_field:
                table.time_partitioning = bigquery.TimePartitioning(
                    type_=bigquery.TimePartitioningType.DAY,
                    field=time_partitioning_field,
                )
                if clustering_fields:
                    table.clustering_fields = clustering_fields

            self.client_bigquery.create_table(table)

    def delete_bq_table(self, dataset_id: str, table_id: str) -> None:
        """
        Delete a BigQuery table.

        Args:
            dataset_id (str): The name of the dataset.
            table_id (str): The name of the table.
        """
        table_ref = self.client_bigquery.dataset(dataset_id).table(table_id)
        self.client_bigquery.delete_table(table_ref)

    @staticmethod
    def update_bq_table_schema(
        dataset_id: str, table_id: str, schema_path: str
    ) -> None:
        """
        Update the schema of a BigQuery table.

        Args:
            dataset_id (str): The name of the dataset.
            table_id (str): The name of the table.
            schema_path (str): The path to the updated JSON schema file.
        """
        os.system(f"bq update {dataset_id}.{table_id} {schema_path}")

    def bq_to_gcs_export(
        self,
        gcs_bucket: str,
        blob_name: str,
        dataset_id: str,
        table_id: str,
        destination_format: str,
        location: str = "EU",
        compression: Optional[str] = None,
        labels: Optional[Dict[str, str]] = None,
        field_delimiter: Optional[str] = None,
        print_header: Optional[bool] = True,
        multiple_files: Optional[bool] = None,
    ) -> None:
        """
        Export a BigQuery table to Google Cloud Storage.

        Args:
            gcs_bucket (str): The name of the GCS bucket.
            blob_name (str): The name of the blob (file) in the bucket.
            dataset_id (str): The name of the dataset.
            table_id (str): The name of the table.
            destination_format (str): The format of the exported data.
            location (str): The location of the GCS bucket. Defaults to "EU".
            compression (Optional[str], optional): The type of compression to use. Defaults to None.
            labels (Optional[Dict[str, str]], optional): A set of labels to apply to the exported data. Default None.
            field_delimiter (Optional[str], optional): Delimiter to use between fields in the data. Default None.
            print_header (Optional[bool], optional): To print a header row in the data. Default True.
            multiple_files (Optional[bool], optional): Export the data to multiple files. Defaults None.
        """
        job_config = bigquery.job.ExtractJobConfig()
        job_config.destination_format = destination_format
        if compression:
            job_config.compression = compression

        if labels:
            job_config.labels = labels

        if destination_format == "CSV":
            if field_delimiter:
                job_config.field_delimiter = field_delimiter

            job_config.print_header = print_header
            if multiple_files:
                gcs_uri = (
                    f"gs://{gcs_bucket}/{blob_name}_*.csv"
                    if multiple_files
                    else f"gs://{gcs_bucket}/{blob_name}.csv"
                )
            else:
                gcs_uri = f"gs://{gcs_bucket}/{blob_name}.csv"

        elif destination_format == "NEWLINE_DELIMITED_JSON":
            if multiple_files:
                gcs_uri = (
                    f"gs://{gcs_bucket}/{blob_name}_*.json"
                    if multiple_files
                    else f"gs://{gcs_bucket}/{blob_name}.json"
                )
            else:
                gcs_uri = f"gs://{gcs_bucket}/{blob_name}.json"

        table_ref = self.client_bigquery.dataset(dataset_id).table(table_id)
        self.client_bigquery.extract_table(
            table_ref, gcs_uri, location=location, job_config=job_config
        ).result()

    def bq_query_job(
        self,
        dataset_id: str,
        table_id: str,
        write_disposition: str,
        location: str = "EU",
        time_partitioning_field: Optional[str] = None,
        clustering_fields: Optional[List[str]] = None,
        sql_file_path: Optional[str] = None,
        sql: Optional[str] = None,
    ) -> None:
        """
        Execute a query job in BigQuery.

        Args:
            dataset_id (str): The name of the dataset.
            table_id (str): The name of the table.
            write_disposition (str): The write disposition for the query.
            location (str): The location of the query. Defaults to "EU".
            time_partitioning_field (Optional[str], optional): Field used for time partitioning. Default None.
            clustering_fields (Optional[List[str]], optional): A list of fields to use for clustering. Default None.
            sql_file_path (Optional[str], optional): The path to the SQL file to be used for the query. Default None.
            sql (Optional[str], optional): The SQL query to be executed. Defaults to None.
        """
        job_config = bigquery.QueryJobConfig()
        sql = self._load_sql(sql_file_path, sql)
        table_id = self._get_table_id(table_id)
        table_ref = self.client_bigquery.dataset(dataset_id).table(table_id)
        job_config.destination = table_ref
        job_config.write_disposition = self._get_write_disposition(write_disposition)

        if time_partitioning_field:
            job_config.time_partitioning = bigquery.table.TimePartitioning(
                field=time_partitioning_field
            )

        if clustering_fields:
            job_config.clustering_fields = clustering_fields

        self.client_bigquery.query(
            sql, location=location, job_config=job_config
        ).result()

    def batch_import_json_to_bq(
        self,
        data: List[Dict[Any, Any]],
        dataset_id: str,
        table_id: str,
        location: str = "EU",
        write_disposition: str = "WRITE_APPEND",
        ignore_unknown_values: bool = False,
        time_partitioning_field: Optional[str] = None,
        partition_type: str = "DAY",
        add_record_ts: bool = True,
        table_schema: Optional[List[bigquery.SchemaField]] = None,
        record_ts_field_name: str = "record_timestamp",
        schema_path: Optional[str] = None,
        autodetect_schema: Optional[bool] = None,
    ) -> None:
        """
        Import a batch of JSON data into BigQuery.

        Args:
            data (List[Dict[Any, Any]]): The data to import.
            dataset_id (str): The name of the dataset.
            table_id (str): The name of the table.
            location (str): The location of the dataset. Defaults to "EU".
            write_disposition (str): Write disposition to use for the import job. Default "WRITE_APPEND".
            ignore_unknown_values (bool): Whether to ignore unknown values in the data. Defaults to False.
            time_partitioning_field (str, optional): The name of the field used for time partitioning. Defaults to None.
            partition_type (str): The type of partitioning to use. Defaults to "DAY".
            add_record_ts (bool): Whether to add a record timestamp to each row. Defaults to True.
            table_schema (List[bigquery.SchemaField], optional): The schema of the table. Defaults to None.
            record_ts_field_name (str): The name of the record timestamp field. Default "record_timestamp".
            schema_path (str, optional): The path to the JSON schema file. Defaults to None.
            autodetect_schema (bool, optional): If BQ auto detect should be used
        """
        if add_record_ts:
            for row in data:
                row[record_ts_field_name] = str(datetime.datetime.now())

        results_newline_json = "\n".join([json.dumps(row) for row in data])
        table_ref = self.client_bigquery.dataset(dataset_id).table(table_id)
        job_config = bigquery.LoadJobConfig()
        job_config.source_format = bigquery.SourceFormat.NEWLINE_DELIMITED_JSON
        job_config.write_disposition = getattr(
            bigquery.WriteDisposition, write_disposition
        )
        job_config.schema_update_options = [
            bigquery.SchemaUpdateOption.ALLOW_FIELD_ADDITION
        ]

        # Load Schema file
        if schema_path:
            job_config.schema = self.client_bigquery.schema_from_json(schema_path)
        elif table_schema:
            job_config.schema = table_schema
        elif autodetect_schema is True:
            job_config.autodetect = True

        job_config.ignore_unknown_values = ignore_unknown_values
        field = time_partitioning_field or record_ts_field_name
        job_config.time_partitioning = (
            bigquery.table.TimePartitioning(field=field, type_=partition_type)
            if field
            else None
        )
        byte_file = BytesIO(results_newline_json.encode())
        byte_file.seek(0)
        self.client_bigquery.load_table_from_file(
            file_obj=byte_file,
            destination=table_ref,
            location=location,
            job_config=job_config,
        ).result()

    @staticmethod
    def _load_sql(
        sql_file_path: Optional[str] = None, sql: Optional[str] = None
    ) -> Optional[str]:
        """
        Load SQL from the given file path, or returns the provided SQL.

        Args:
            sql_file_path (Optional[str]): The path to the SQL file. Defaults to None.
            sql (Optional[str]): The SQL string. Defaults to None.

        Returns:
            Optional[str]: The loaded SQL string or None if both arguments are None.
        """
        if sql_file_path:
            with open(sql_file_path, mode="r", encoding="utf-8-sig") as file:
                sql = file.read()
        return sql

    @staticmethod
    def _get_write_disposition(write_disposition: str):
        """
        Return the BigQuery WriteDisposition corresponding to the provided string.

        Args:
            write_disposition (str): The write disposition string.

        Returns:
            bigquery.WriteDisposition: The corresponding WriteDisposition enum member.
        """
        write_disposition_mapping = {
            "WRITE_TRUNCATE": bigquery.WriteDisposition.WRITE_TRUNCATE,
            "WRITE_EMPTY": bigquery.WriteDisposition.WRITE_EMPTY,
        }
        return write_disposition_mapping.get(
            write_disposition, bigquery.WriteDisposition.WRITE_APPEND
        )

    @staticmethod
    def _get_table_id(table_id: str):
        """
        Add current date to the table name if it ends with "_*" or "$".

        Args:
            table_id (str): The original table name.

        Returns:
            str: The table name with date appended if it ends with "_*" or "$".
        """
        if table_id.endswith("_*"):
            table_id += "_" + datetime.datetime.utcnow().strftime("%Y%m%d")
        elif table_id.endswith("$"):
            table_id += datetime.datetime.now().strftime("%Y%m%d")
        return table_id

    def _parse_bq_json_schema(self, schema_filename: str) -> List[bigquery.SchemaField]:
        """
        Parse a BigQuery schema from a JSON file.

        Args:
            schema_filename (str): The filename of the JSON schema.

        Returns:
            List[bigquery.SchemaField]: A list of SchemaField objects.
        """
        with open(schema_filename, "r") as infile:
            jsonschema = json.load(infile)
        return [self._get_field_schema(field) for field in jsonschema]

    def _get_field_schema(
        self, field: Dict[str, Union[str, List[Dict[str, str]]]]
    ) -> bigquery.SchemaField:
        """
        Return a SchemaField from a dictionary representation.

        Args:
            field (Dict[str, Union[str, List[Dict[str, str]]]]): The dictionary representation of a SchemaField.

        Returns:
            bigquery.SchemaField: The SchemaField object.
        """
        name = field["name"]
        field_type = field.get("type", "STRING")
        mode = field.get("mode", "NULLABLE")
        fields = field.get("fields", [])
        subschema = [self._get_field_schema(f) for f in fields] if fields else []
        return bigquery.SchemaField(
            name=name, field_type=field_type, mode=mode, fields=subschema
        )
