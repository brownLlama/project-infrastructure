"""This module provides a controller for managing Google Cloud Pub/Sub operations."""

import base64
import json
from typing import List, Optional

from google.cloud import pubsub_v1

from ..quickops_toolkit.logger import get_logger

logger = get_logger(__name__)


class PubSubController:
    """A controller to simplify interactions with Google Cloud Pub/Sub."""

    def __init__(self, project_id: str):
        """
        Initialize the PubSubController with Google Cloud project information.

        Args:
            project_id (str): The Google Cloud project ID.
        """
        self.project_id = project_id
        self.publisher_client = pubsub_v1.PublisherClient()
        self.subscriber_client = pubsub_v1.SubscriberClient()

    def publish_messages(
        self, topic_id: str, messages: List[str], **attrs: Optional[dict]
    ) -> None:
        """
        Publish messages to a specified Pub/Sub topic.

        Args:
            topic_id (str): The ID of the Pub/Sub topic to publish messages to.
            messages (List[str]): A list of messages to publish.
            **attrs (Optional[dict]): Additional attributes to send with the message.
        """
        try:
            topic_path = self.publisher_client.topic_path(self.project_id, topic_id)

            for message in messages:
                string_data = json.dumps(message)
                data = string_data.encode("utf-8")
                future = self.publisher_client.publish(topic_path, data, **attrs)

                logger.info(f"Published message ID: {future.result()}")

        except Exception as e:
            logger.error(f"An error occurred while trying to publish messages: {e}")

    def pull_messages(
        self,
        subscription_id: str,
        max_messages: int = 100,
        return_immediately: bool = False,
    ):
        """
        Pull messages from a specified Pub/Sub subscription.

        Args:
            subscription_id (str): The ID of the Pub/Sub subscription to pull messages from.
            max_messages (int): The maximum number of messages to pull.
            return_immediately (bool): Whether to return immediately if no messages are available.

        Returns:
            tuple: A tuple containing a list of retrieved messages and a list of their corresponding ack IDs.
        """
        subscription_path = self.subscriber_client.subscription_path(
            self.project_id, subscription_id
        )
        retrieved_messages = []

        response = self.subscriber_client.pull(
            subscription=subscription_path,
            max_messages=max_messages,
            return_immediately=return_immediately,
        )

        ack_ids = []

        for received_message in response.received_messages:
            message_data_json = received_message.message.data.decode("utf-8")
            message_data = json.loads(message_data_json)

            retrieved_messages.append(message_data)
            ack_ids.append(received_message.ack_id)

        return retrieved_messages, ack_ids

    @staticmethod
    def transform_push_message(message):
        """
        Transform a message from a push subscription into a usable format.

        Args:
            message (dict): The message received from Pub/Sub.

        Returns:
            dict: The decoded message data.
        """
        # Check if message.data is of type bytes, decode if necessary
        if isinstance(message["data"], str):
            message_data = json.loads(base64.b64decode(message["data"]))
        else:
            # Log an error or raise an exception if message.data is neither bytes nor string
            logger.error(f"Unexpected message data type: {type(message['data'])}")
            raise TypeError("Message data must be bytes or string")

        return message_data

    def acknowledge_messages(self, subscription_id: str, ack_ids: List[str]):
        """
        Acknowledge the reception of messages from a Pub/Sub subscription.

        Args:
            subscription_id (str): The ID of the Pub/Sub subscription.
            ack_ids (List[str]): A list of acknowledgment IDs of messages to acknowledge.
        """
        subscription_path = self.subscriber_client.subscription_path(
            self.project_id, subscription_id
        )

        # Acknowledge all messages at once after processing
        if ack_ids:
            self.subscriber_client.acknowledge(
                subscription=subscription_path, ack_ids=ack_ids
            )
