"""This module provides utilities for generating database schemas and interacting with Cloud SQL databases."""

import datetime
import json
from collections import defaultdict
from typing import Any, Dict, List

import psycopg2
from dateutil.parser import parse
from psycopg2 import sql

from ..quickops_toolkit.logger import get_logger

logger = get_logger(__name__)


class SchemaGenerator:
    """Generates database schema definitions based on sample data."""

    def infer_data_type(self, values: List[Any]) -> str:
        """
        Infer the data type for a PostgreSQL column based on a list of Python values.

        Args:
            values (List[Any]): A list of values from which to infer the column data type.

        Returns:
            str: A string representing the PostgreSQL data type.
        """
        types_encountered = set()

        for value in values:
            if isinstance(value, int):
                if -2147483648 <= value <= 2147483647:
                    types_encountered.add("INTEGER")
                else:
                    types_encountered.add("BIGINT")
            elif isinstance(value, float):
                types_encountered.add("REAL")
            elif isinstance(value, bool):
                types_encountered.add("BOOLEAN")
            elif isinstance(value, (datetime.datetime, datetime.date)):
                types_encountered.add(
                    "TIMESTAMP" if isinstance(value, datetime.datetime) else "DATE"
                )
            elif isinstance(value, list):
                if value:
                    element_type = self.infer_data_type(value)
                    types_encountered.add(f"{element_type}[]")
                else:
                    types_encountered.add("TEXT[]")
            elif isinstance(value, dict):
                types_encountered.add("JSONB")
            elif isinstance(value, str):
                # Attempt to parse the string as a date or timestamp
                date_or_timestamp = self.infer_string_date_or_timestamp(value)
                if date_or_timestamp:
                    types_encountered.add(date_or_timestamp)
                else:
                    # If it's not a recognizable date or timestamp format, default to TEXT
                    types_encountered.add("TEXT")
            else:
                types_encountered.add("TEXT")

        # Priority Logic
        for data_type in [
            "TEXT",
            "JSONB",
            "TEXT[]",
            "JSONB[]",
            "TIMESTAMP[]",
            "DATE[]",
            "REAL[]",
            "BIGINT[]",
            "INTEGER[]",
            "BOOLEAN[]",
            "TIMESTAMP",
            "DATE",
            "REAL",
            "BIGINT",
            "INTEGER",
            "BOOLEAN",
        ]:
            if data_type in types_encountered:
                return data_type
        return "TEXT"  # Default to TEXT if nothing else matched

    @staticmethod
    def infer_string_date_or_timestamp(value):
        """
        Infer if a string value is a DATE or TIMESTAMP for PostgreSQL.

        Args:
            value (str): The string value to analyze.

        Returns:
            Optional[str]: 'DATE', 'TIMESTAMP', 'INTEGER', 'BIGINT', or None
        """
        try:
            # Try parsing the string as a datetime
            parsed_date = parse(value)
            # If it could be parsed, determine if it has a time component
            if parsed_date.time() == datetime.time(0):
                if value.isnumeric():
                    if len(value) < 10:
                        return "INTEGER"
                    else:
                        return "BIGINT"
                return "DATE"
            else:
                return "TIMESTAMP"
        except Exception:
            # If parsing fails, it's not a recognizable date or timestamp
            return None

    def generate_create_table_statement(
        self,
        table_schema: str,
        table_name: str,
        dict_list: List[Dict[str, Any]],
        primary_keys: List[str],
    ) -> str:
        """
        Generate a SQL statement to create a new table with inferred column types.

        Args:
            table_schema (str): The schema of the table.
            table_name (str): The name of the table.
            dict_list (List[Dict[str, Any]]): A list of dictionaries representing sample data for the table.
            primary_keys (List[str]): A list of columns that should be used as the primary key.

        Returns:
            str: A string containing the CREATE TABLE SQL statement.
        """
        if not dict_list:
            raise ValueError(
                "The list of dictionaries is empty. Cannot generate schema."
            )

        # Analyze the first 1000 rows or all rows if less than 1000
        sample_size = min(1000, len(dict_list))
        sample_data = dict_list[:sample_size]

        # Collect values for each column across the sample
        column_values = defaultdict(list)
        for row in sample_data:
            for column, value in row.items():
                column_values[column].append(value)

        # Infer data type for each column
        columns = [
            f'"{column}" {self.infer_data_type(values)}'
            + (
                " PRIMARY KEY"
                if column in primary_keys and len(primary_keys) == 1
                else ""
            )
            for column, values in column_values.items()
        ]
        columns_str = ", ".join(columns)
        create_statement = (
            f'CREATE TABLE IF NOT EXISTS "{table_schema}"."{table_name}" ({columns_str}'
        )

        if len(primary_keys) > 1:
            primary_keys_str = ", ".join([f'"{key}"' for key in primary_keys])
            create_statement += f", PRIMARY KEY ({primary_keys_str})"

        create_statement += ");"

        return create_statement


class CloudSQLController:
    """Manages connections and operations for a Cloud SQL database."""

    def __init__(self, db_params: Dict[str, Any]) -> None:
        """
        Initialize the Cloud SQL controller with database connection parameters.

        Args:
            db_params (Dict[str, Any]): A dictionary containing database connection parameters.
        """
        self.db_params = db_params
        self.conn = self._create_connection()

    @staticmethod
    def format_to_sql_dt(dt_with_ns):
        """Convert DateTimeWithNanoSeconds from Firestore to formatted string for BigQuery."""
        if hasattr(dt_with_ns, "seconds") and hasattr(dt_with_ns, "nanoseconds"):
            dt_object = datetime.datetime.utcfromtimestamp(
                dt_with_ns.seconds + dt_with_ns.nanoseconds / 1e9
            )
            return dt_object.strftime("%Y-%m-%d %H:%M:%S.%f")

        elif isinstance(
            dt_with_ns, datetime.datetime
        ):  # If it's already a datetime object
            return dt_with_ns.strftime("%Y-%m-%d %H:%M:%S.%f")

        elif isinstance(dt_with_ns, int):  # If it's a UNIX timestamp
            if dt_with_ns > 10**12:  # Likely in milliseconds
                dt_with_ns /= 1000
            dt_object = datetime.datetime.utcfromtimestamp(dt_with_ns)
            return dt_object.strftime("%Y-%m-%d %H:%M:%S.%f")

        return dt_with_ns  # If it's neither, return it as is

    def recursive_fix_time_format(
        self, data: Dict[str, Any], timestamp_columns: List[str]
    ) -> Dict[str, Any]:
        """
        Recursively fix the format of timestamp fields in a nested data structure.

        Args:
            data (Dict[str, Any]): The data structure containing timestamps to fix.
            timestamp_columns (List[str]): A list of column names containing timestamp values.

        Returns:
            Dict[str, Any]: The data structure with formatted timestamps.
        """
        for key, value in data.items():
            if key in timestamp_columns:
                data[key] = self.format_to_sql_dt(value)
            elif isinstance(value, dict):
                data[key] = self.recursive_fix_time_format(value, timestamp_columns)
        return data

    def _create_connection(self):
        try:
            return psycopg2.connect(**self.db_params)
        except Exception as e:
            logger.error(f"The error '{e}' occurred", exc_info=True)
            return None

    def _execute_query(self, query: str, params: tuple = ()):
        with self.conn.cursor() as cursor:
            try:
                cursor.execute(query, params)
                self.conn.commit()
            except Exception as e:
                logger.error(
                    f"The error '{e}' occurred for: : \n {query}", exc_info=True
                )
                self.conn.rollback()
                raise e

    def _execute_read_query(self, query: str, params: tuple = ()) -> List[Any]:
        with self.conn.cursor() as cursor:
            try:
                cursor.execute(query, params)
                return cursor.fetchall()
            except Exception as e:
                logger.error(
                    f"The error '{e}' occurred for: : \n {query}", exc_info=True
                )
                raise e

    def ensure_schema_exists(self, table_schema: str) -> None:
        """
        Ensure that a given database schema exists, creating it if necessary.

        Args:
            table_schema (str): The name of the schema to check or create.
        """
        with self.conn.cursor() as cursor:
            check_schema_query = sql.SQL(
                "SELECT schema_name FROM information_schema.schemata WHERE schema_name = %s;"
            )
            create_schema_query = sql.SQL("CREATE SCHEMA IF NOT EXISTS {}").format(
                sql.Identifier(table_schema)
            )
            try:
                cursor.execute(check_schema_query, (table_schema,))
                if cursor.fetchone() is None:
                    cursor.execute(create_schema_query)
                    self.conn.commit()
                    logger.info(f"Schema '{table_schema}' created.")
            except Exception as e:
                logger.error(
                    f"Error occurred while checking/creating schema: {e}", exc_info=True
                )
                self.conn.rollback()
                raise e

    def does_table_exist(self, table_schema: str, table_name: str) -> bool:
        """
        Check if a specific table exists within the schema.

        Args:
            table_schema (str): The name of the schema.
            table_name (str): The name of the table.

        Returns:
            bool: True if the table exists, False otherwise.
        """
        with self.conn.cursor() as cursor:
            query = sql.SQL(
                "SELECT EXISTS (SELECT * FROM information_schema.tables WHERE table_schema = %s AND table_name = %s);"
            )
            try:
                cursor.execute(query, (table_schema, table_name))
                return cursor.fetchone()[0]
            except Exception as e:
                logger.error(
                    f"Error occurred while checking if table exists: {e}", exc_info=True
                )
                return False

    def _nested_dict_to_json_string(self, data):
        if isinstance(data, dict):
            for key, value in data.items():
                # Directly serialize nested dicts without further recursion
                if isinstance(value, dict):
                    data[key] = json.dumps(value)
                # For lists, process each item if it's a dict; serialize it
                elif isinstance(value, list):
                    data[key] = [
                        json.dumps(item) if isinstance(item, dict) else item
                        for item in value
                    ]
                # No change for non-nested items or non-dict items in lists
        elif isinstance(data, list):
            # If the method is somehow directly called with a list, process each item similarly
            return [
                (
                    self._nested_dict_to_json_string(item)
                    if isinstance(item, dict)
                    else item
                )
                for item in data
            ]
        return data

    def batch_insert(
        self,
        table_schema: str,
        table_name: str,
        data_list: List[Dict[str, Any]],
        primary_keys: List[str],
        on_conflict_action: str = "ignore",
        timestamp_columns: List[str] = None,
    ) -> None:
        """
        Insert a batch of data into a specified table, with conflict handling.

        Args:
            table_schema (str): The schema of the table.
            table_name (str): The name of the table.
            data_list (List[Dict[str, Any]]): A list of dictionaries representing the data to insert.
            primary_keys (List[str]): A list of primary key columns.
            on_conflict_action (str): The action to take on a conflict ('ignore' or 'update').
            timestamp_columns (List[str]): A list of columns that contain timestamp data.
        """
        if not data_list:
            logger.info("No data provided for upsert. Will skip.")
            return

        if not self.does_table_exist(table_schema, table_name):
            self.ensure_schema_exists(table_schema)
            schema_gen = SchemaGenerator()
            create_table_query = schema_gen.generate_create_table_statement(
                table_schema, table_name, data_list, primary_keys
            )
            self._execute_query(create_table_query)

        if timestamp_columns:
            for i in range(len(data_list)):
                data_list[i] = self.recursive_fix_time_format(
                    data_list[i], timestamp_columns
                )

        if on_conflict_action == "ignore":
            on_conflict_clause = "ON CONFLICT DO NOTHING"
        elif on_conflict_action == "update":
            primary_keys_str = ", ".join([f'"{key}"' for key in primary_keys])
            update_clause = ", ".join(
                [
                    f'"{col}" = EXCLUDED."{col}"'
                    for col in data_list[0].keys()
                    if col not in primary_keys
                ]
            )
            on_conflict_clause = (
                f"ON CONFLICT ({primary_keys_str}) DO UPDATE SET {update_clause}"
            )
        else:
            raise ValueError(f"Invalid on_conflict_action: {on_conflict_action}")

        # Retrieve columns and their data types from the information schema
        with self.conn.cursor() as cursor:
            cursor.execute(
                "SELECT column_name, udt_name AS data_type "
                "FROM information_schema.columns "
                "WHERE table_schema = %s AND table_name = %s;",
                (table_schema, table_name),
            )
            columns_info = cursor.fetchall()

            # Map columns to their types
            column_types = {col[0]: col[1] for col in columns_info}
            table_columns = [f'"{col}"' for col in column_types]

            # Build the query
            columns_str = ", ".join(table_columns)
            values = []
            for data in data_list:
                # Pre-process data to handle jsonb and jsonb[] columns
                pre_processed_data = self._preprocess_data_for_insert(
                    data, column_types
                )
                processed_data = self._nested_dict_to_json_string(pre_processed_data)
                row_values = [
                    processed_data.get(col.replace('"', ""), None)
                    for col in column_types
                ]
                values.append(row_values)

            # Construct the VALUES part of the SQL command
            values_template = ", ".join(
                [
                    (
                        "%s::" + column_types[col.replace('"', "")]
                        if not column_types[col.replace('"', "")].startswith("_")
                        else "%s::"
                        + column_types[col.replace('"', "")].replace("_", "")
                        + "[]"
                    )
                    for col in column_types
                ]
            )
            query_values_part = ", ".join(
                cursor.mogrify(f"({values_template})", val).decode("utf-8")
                for val in values
            )

            query = f'INSERT INTO "{table_schema}"."{table_name}" ({columns_str}) VALUES {query_values_part}'
            query += f" {on_conflict_clause};"

            try:
                cursor.execute(query)
                self.conn.commit()
                logger.info(
                    f"Batch upsert executed successfully with action '{on_conflict_action}'"
                )
            except Exception as e:
                logger.error(
                    f"The error '{e}' occurred during batch upsert with action '{on_conflict_action}'. Query: {query}",
                    exc_info=True,
                )
                raise Exception(
                    f"Error occurred during batch upsert with action '{on_conflict_action}' ({e})"
                )

    @staticmethod
    def _preprocess_data_for_insert(data, column_types):
        processed = {}
        for key, value in data.items():
            if key in column_types:
                if column_types[key] == "jsonb":
                    processed[key] = (
                        json.dumps(value) if isinstance(value, (dict, list)) else value
                    )
                elif column_types[key].endswith("[]"):
                    processed[key] = value if isinstance(value, list) else [value]
                else:
                    processed[key] = value
            else:
                processed[key] = value
        return processed

    def close(self):
        """Close the database connection."""
        if self.conn is not None:
            self.conn.close()

    def __del__(self):
        """Close the database connection when the object is deleted."""
        self.close()
