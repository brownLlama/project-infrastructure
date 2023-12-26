"""
MonitoringController class for interacting with Google Cloud Monitoring.

It includes functionalities to create metric descriptors, check for their existence, log metrics
to Cloud Monitoring, and handle retries for time series data creation. The MonitoringController
class provides an interface to manage custom metrics in a Google Cloud project, supporting
operations like creating custom metric descriptors, logging data points to these metrics, and
handling retries with exponential backoff strategy for robustness.
"""

from datetime import datetime

from google.api import label_pb2 as ga_label
from google.api import metric_pb2 as ga_metric
from google.api_core import exceptions, retry
from google.api_core.exceptions import NotFound
from google.cloud import monitoring_v3
from google.cloud.monitoring_v3.types import Point, TimeInterval
from google.protobuf import timestamp_pb2

from ..quickops_toolkit.logger import get_logger

logger = get_logger(__name__)


class MonitoringController:
    """
    A controller for managing interactions with Google Cloud Monitoring.

    This class provides methods to create and manage metric descriptors, query
    for their existence, and log metrics to Cloud Monitoring. It also supports
    handling retries for creating time series data, which is crucial for
    ensuring robustness in communication with Google Cloud Monitoring services.

    Attributes:
        project_id (str): The ID of the Google Cloud project.
        client (monitoring_v3.MetricServiceClient): The client for interacting
            with the Google Cloud Monitoring API.
        project_name (str): The name of the Google Cloud project.
        metric_descriptors (dict): A cache of created metric descriptors.

    Methods:
        create_metric_descriptor: Create a new metric descriptor in Cloud Monitoring.
        metric_descriptor_exists: Check if a metric descriptor exists.
        _create_time_series_with_retry: Create a time series with retry on failure.
        log_to_cloud_monitoring: Log a metric to Cloud Monitoring.
    """

    def __init__(self, project_id):
        """
        Initialize the MonitoringController with a specific Google Cloud project ID.

        Sets up the MetricServiceClient and defines the project name. It also initializes
        a dictionary to cache metric descriptors.

        Args:
            project_id (str): The ID of the Google Cloud project to monitor.
        """
        self.project_id = project_id
        self.client = monitoring_v3.MetricServiceClient()
        self.project_name = f"projects/{project_id}"
        self.metric_descriptors = {}

    def create_metric_descriptor(
        self, metric_type, metric_kind, value_type, description
    ):
        """
        Create a new metric descriptor in Google Cloud Monitoring.

        If the metric type already exists in the cache, it returns the existing descriptor.
        Otherwise, it creates a new metric descriptor with the specified parameters.

        Args:
            metric_type (str): The type of the metric, e.g., 'custom.googleapis.com/my_metric'.
            metric_kind (enum): The kind of metric, e.g., ga_metric.MetricDescriptor.MetricKind.GAUGE.
            value_type (enum): The value type of the metric, e.g., ga_metric.MetricDescriptor.ValueType.DOUBLE.
            description (str): A brief description of the metric.

        Returns:
            The created or existing metric descriptor.
        """
        if metric_type in self.metric_descriptors:
            return self.metric_descriptors[metric_type]

        descriptor = ga_metric.MetricDescriptor()
        descriptor.type = f"custom.googleapis.com/{metric_type}"
        descriptor.metric_kind = metric_kind
        descriptor.value_type = value_type
        descriptor.description = description

        labels = ga_label.LabelDescriptor()
        labels.key = "environment"
        labels.value_type = ga_label.LabelDescriptor.ValueType.STRING
        labels.description = "The environment in which the metric is reported"
        descriptor.labels.append(labels)

        descriptor = self.client.create_metric_descriptor(
            name=self.project_name, metric_descriptor=descriptor
        )
        self.metric_descriptors[metric_type] = descriptor
        return descriptor

    def metric_descriptor_exists(self, metric_type):
        """Check if the metric descriptor exists in Cloud Monitoring."""
        try:
            descriptor = self.client.get_metric_descriptor(
                name=f"{self.project_name}/metricDescriptors/custom.googleapis.com/{metric_type}"
            )
            return descriptor is not None
        except NotFound:
            return False

    # Define a retryable function with exponential backoff
    @staticmethod
    @retry.Retry(
        predicate=retry.if_exception_type(exceptions.InternalServerError),
        initial=1.0,  # Start with a 1 second wait
        maximum=60.0,  # Maximum wait of 60 seconds
        multiplier=2.0,  # Double the wait each retry
        deadline=300.0,  # Total deadline of 5 minutes
    )
    def _create_time_series_with_retry(client, project_name, time_series):
        client.create_time_series(name=project_name, time_series=time_series)

    def log_to_cloud_monitoring(
        self,
        metric_type,
        value,
        metric_kind,
        value_type,
        description,
        labels=None,
        custom_time=None,
    ):
        """
        Log a metric to Google Cloud Monitoring.

        This method ensures that a metric descriptor exists before logging the metric.
        It handles the creation of time series data for the specified metric and
        logs it to Google Cloud Monitoring. The method supports custom labels and
        custom time for the metric data.

        Args:
            metric_type (str): The type of the metric to log.
            value (Any): The value of the metric to log. The type depends on value_type.
            metric_kind (enum): The kind of metric (e.g., GAUGE, CUMULATIVE).
            value_type (enum): The value type of the metric (e.g., INT64, DOUBLE).
            description (str): A description of the metric.
            labels (dict, optional): A dictionary of labels for the metric. Defaults to None.
            custom_time (datetime, optional): The time of the metric data point. Defaults to None.
                If None, the current UTC time is used.
        """
        logger.debug(f"Attempting to log to Cloud Monitoring - {metric_type}")
        # Check if the metric descriptor exists, create if it does not
        if not self.metric_descriptor_exists(metric_type):
            # Here, you'd call create_metric_descriptor with the parameters you want
            # This assumes you've predefined them or you pass them into this method.
            self.create_metric_descriptor(
                metric_type, metric_kind, value_type, description
            )

        series = monitoring_v3.types.TimeSeries()
        series.metric.type = f"custom.googleapis.com/{metric_type}"
        series.resource.type = "global"
        series.resource.labels["project_id"] = self.project_id

        if labels is not None:
            for label_key, label_value in labels.items():
                series.metric.labels[label_key] = label_value

        point = Point()

        if value_type == "INT64":
            point.value.int64_value = int(value)
        elif value_type == "DOUBLE":
            point.value.double_value = float(value)

        interval = TimeInterval()

        # Set the interval end time using FromDatetime
        if custom_time is not None:
            # Make sure custom_time is a datetime object
            if not isinstance(custom_time, datetime):
                custom_time = datetime.utcfromtimestamp(custom_time)
        else:
            custom_time = datetime.utcnow()

        timestamp = timestamp_pb2.Timestamp()
        timestamp.FromDatetime(custom_time)
        interval.end_time = timestamp

        point.interval = interval

        series.points.append(point)

        # Batching write operations could be implemented here if necessary
        # Use the retryable function instead of client.create_time_series directly
        try:
            self._create_time_series_with_retry(
                self.client, self.project_name, [series]
            )
            logger.debug(
                f"Successful logging to Cloud Monitoring - {metric_type} - {value}"
            )
        except Exception as e:
            logger.error(
                f"Failed to log to Cloud Monitoring after retries - {metric_type} - {value} - {e}"
            )
            # Handle or raise the exception appropriately
