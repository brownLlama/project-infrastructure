"""
CloudTasksController: A controller for handling Google Cloud Tasks operations.

This module provides a `CloudTasksController` class to abstract various operations on Google Cloud Tasks, such as
creating a new task with an HTTP target, listing tasks in a queue, and deleting a specific task.

The controller offers the following functionalities:
    - Initialize a CloudTasks client using the specified GCP project ID, location, and queue ID.
    - Create tasks with optional payload and scheduling delay.
    - List all tasks in the specified queue.
    - Delete tasks by their full name.

The module uses the Google Cloud Tasks v2 API and leverages `google.cloud.tasks_v2` and `google.protobuf.timestamp_pb2`
for creating and managing tasks.

Classes:
    CloudTasksController: Main class encapsulating all Google Cloud Tasks related operations.
"""

import datetime

from gaming_academy_utilpack.quickops_toolkit.logger import get_logger
from google.cloud import tasks_v2
from google.protobuf import timestamp_pb2
from google.protobuf.duration_pb2 import Duration

logger = get_logger(__name__)


class CloudTasksController:
    """
    CloudTasksController: A controller for handling Google Cloud Tasks operations.

    Args:
        project_id (str): The GCP project ID.
    """

    def __init__(self, project_id):
        """
        Initialize the CloudTasksController.

        Args:
            project_id (str): The GCP project ID.

        """
        self.client = tasks_v2.CloudTasksClient()
        self.project_id = project_id

    def create_task(
        self,
        location,
        queue,
        url,
        payload=None,
        in_seconds=None,
        deadline_in_seconds=None,
    ):
        """
        Create a task with an HTTP target.

        Args:
            location (str): The location ID where the task queue resides.
            queue (str): The task queue ID.
            url (str): The endpoint URL where the task will send a POST request.
            payload (str, optional): The payload to be sent in the POST request. Defaults to None.
            in_seconds (int, optional): Delay in seconds before the task is dispatched. Defaults to None.
            deadline_in_seconds (int, optional): The maximum amount of time in seconds allowed for
                                                 a successful (HTTP 200) worker response.

        Returns:
            google.cloud.tasks_v2.types.Task: The created task object.

        """
        parent = self.client.queue_path(self.project_id, location, queue)
        task = {"http_request": {"http_method": tasks_v2.HttpMethod.POST, "url": url}}

        if payload is not None:
            # The API expects bytes payload, so we encode it.
            task["http_request"]["body"] = payload.encode()

        if in_seconds is not None:
            # Convert "seconds from now" into an actual timestamp.
            d = datetime.datetime.utcnow() + datetime.timedelta(seconds=in_seconds)
            timestamp = timestamp_pb2.Timestamp()
            timestamp.FromDatetime(d)
            task["schedule_time"] = timestamp

        if deadline_in_seconds is not None:
            duration = Duration()
            duration.seconds = deadline_in_seconds
            task["dispatch_deadline"] = duration

        response = self.client.create_task(request={"parent": parent, "task": task})
        return response

    def list_tasks(self, location, queue):
        """
        List tasks in the queue.

        Args:
            location (str): The location ID where the task queue resides.
            queue (str): The task queue ID.

        Returns:
            list[google.cloud.tasks_v2.types.Task]: List of task objects in the queue.

        """
        parent = self.client.queue_path(self.project_id, location, queue)
        response = self.client.list_tasks(request={"parent": parent})
        return response

    def delete_task(self, location, queue, task_id):
        """
        Delete a specific task by its task_id, location, and queue.

        Args:
            location (str): The location ID where the task queue resides.
            queue (str): The task queue ID.
            task_id (str): The ID of the task to be deleted.

        """
        task_name = self.client.task_path(self.project_id, location, queue, task_id)
        self.client.delete_task(request={"name": task_name})

    def get_task_count(self, location, queue):
        """
        Get the number of tasks in a specific queue.

        Args:
            location (str): The location ID where the task queue resides.
            queue (str): The task queue ID.

        Returns:
            int: The number of tasks in the queue.
        """
        parent = self.client.queue_path(self.project_id, location, queue)
        tasks = self.client.list_tasks(request={"parent": parent})
        task_count = sum(1 for _ in tasks)
        return task_count

    def update_max_concurrent_dispatches(
        self, location, queue, max_concurrent_dispatches
    ):
        """
        Update the maximum concurrent dispatches for a specific queue.

        Args:
            location (str): The location ID where the task queue resides.
            queue (str): The task queue ID.
            max_concurrent_dispatches (int): The new maximum number of concurrent task dispatches.

        Returns:
            Any: The updated queue.
        """
        queue_path = self.client.queue_path(self.project_id, location, queue)
        queue = self.client.get_queue(request={"name": queue_path})
        queue.rate_limits.max_concurrent_dispatches = max_concurrent_dispatches
        updated_queue = self.client.update_queue(queue=queue)
        return updated_queue
