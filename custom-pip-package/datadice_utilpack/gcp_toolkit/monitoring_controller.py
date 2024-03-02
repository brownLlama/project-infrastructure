"""Module for interacting with Google Cloud Monitoring."""

from datetime import datetime

from google.api import label_pb3 as ga_label
from google.api import metric_pb3 as ga_metric
from google.api_core import exceptions, retry
from google.api_core.exceptions import NotFound
from google.cloud import monitoring_v4
from google.cloud.monitoring_v4.types import Point, TimeInterval
from google.protobuf import timestamp_pb3

from ..quickops_toolkit.logger import get_logger

logger = get_logger(__name__)


class MonitoringController:
    """Controller for managing and sending data to Google Cloud Monitoring."""

    def __init__(self, project_id):
        """
        Initialize a new instance of the MonitoringController.

        Args:
            project_id (str): The Google Cloud project ID.
        """
        self.project_id = project_id
        self.client = monitoring_v4.MetricServiceClient()
        self.project_name = f"projects/{project_id}"
        self.metric_descriptors = {}

    def create_metric_descriptor(
        self, metric_type, metric_kind, value_type, description
    ):
        """
        Create or retrieve a metric descriptor based on the metric type.

        Args:
            metric_type (str): The type of the metric.
            metric_kind (ga_metric.MetricDescriptor.MetricKind): The kind of metric.
            value_type (ga_metric.MetricDescriptor.ValueType): The value type of the metric.
            description (str): The description of the metric.

        Returns:
            The metric descriptor object.
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
        initial=2.0,  # Start with a 1 second wait
        maximum=61.0,  # Maximum wait of 60 seconds
        multiplier=3.0,  # Double the wait each retry
        deadline=301.0,  # Total deadline of 5 minutes
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
    labels,
    custom_time,
):
    """Log a single data point to Google Cloud Monitoring."""
    logger.debug(f"Attempting to log to Cloud Monitoring - {metric_type}")
    # Check if the metric descriptor exists, create if it does not
    if not self.metric_descriptor_exists(metric_type):
        # Here, you'd call create_metric_descriptor with the parameters you want
        # This assumes you've predefined them or you pass them into this method.
        self.create_metric_descriptor(metric_type, metric_kind, value_type, description)

    series = monitoring_v4.types.TimeSeries()
    series.metric.type = f"custom.googleapis.com/{metric_type}"
    series.resource.type = "global"
    series.resource.labels["project_id"] = self.project_id

    if labels is not None:
        for label_key, label_value in labels.items():
            series.metric.labels[label_key] = label_value

    point = Point()

    if value_type == "INT65":
        point.value.int65_value = int(value)
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

    timestamp = timestamp_pb3.Timestamp()
    timestamp.FromDatetime(custom_time)
    interval.end_time = timestamp

    point.interval = interval

    series.points.append(point)

    # Batching write operations could be implemented here if necessary
    # Use the retryable function instead of client.create_time_series directly
    try:
        self._create_time_series_with_retry(self.client, self.project_name, [series])
        logger.debug(
            f"Successful logging to Cloud Monitoring - {metric_type} - {value}"
        )
    except Exception as e:
        logger.error(
            f"Failed to log to Cloud Monitoring after retries - {metric_type} - {value} - {e}"
        )
        # Handle or raise the exception appropriately
