"""GCP PubSubController for managing messages on Pub/Sub."""

from google.cloud import pubsub_v1


class PubSubController:
    """Controller for GCP Pub/Sub operations."""

    def __init__(self, project_id: str):
        """
        Initialize a PubSubController.

        Args:
            project_id (str): The GCP project ID.

        """
        self.project_id = project_id
        self.publisher = pubsub_v1.PublisherClient()
        self.subscriber = pubsub_v1.SubscriberClient()

    def create_topic(self, topic_name: str) -> str:
        """
        Create a new topic.

        Args:
            topic_name (str): The name of the topic to create.

        Returns:
            str: The created topic name.

        """
        topic_path = self.publisher.topic_path(self.project_id, topic_name)
        topic = self.publisher.create_topic(request={"name": topic_path})
        return topic.name

    def delete_topic(self, topic_name: str) -> None:
        """
        Delete a topic.

        Args:
            topic_name (str): The name of the topic to delete.

        """
        topic_path = self.publisher.topic_path(self.project_id, topic_name)
        self.publisher.delete_topic(request={"topic": topic_path})

    def publish_message(self, topic_name: str, message: str) -> str:
        """
        Publish a message to a topic.

        Args:
            topic_name (str): The name of the topic.
            message (str): The message to publish.

        Returns:
            str: The ID of the published message.

        """
        topic_path = self.publisher.topic_path(self.project_id, topic_name)
        future = self.publisher.publish(topic_path, message.encode("utf-8"))
        return future.result()

    def create_subscription(self, topic_name: str, subscription_name: str) -> str:
        """
        Create a new subscription to a topic.

        Args:
            topic_name (str): The name of the topic.
            subscription_name (str): The name of the subscription.

        Returns:
            str: The name of the created subscription.

        """
        topic_path = self.publisher.topic_path(self.project_id, topic_name)
        subscription_path = self.subscriber.subscription_path(
            self.project_id, subscription_name
        )
        subscription = self.subscriber.create_subscription(
            request={"name": subscription_path, "topic": topic_path}
        )
        return subscription.name

    def delete_subscription(self, subscription_name: str) -> None:
        """
        Delete a subscription.

        Args:
            subscription_name (str): The name of the subscription to delete.

        """
        subscription_path = self.subscriber.subscription_path(
            self.project_id, subscription_name
        )
        self.subscriber.delete_subscription(request={"subscription": subscription_path})

    def acknowledge_messages(self, subscription_name: str, ack_ids: list) -> None:
        """
        Acknowledge the receipt of specific messages.

        Args:
            subscription_name (str): The name of the subscription.
            ack_ids (list): A list of acknowledgment IDs.

        """
        subscription_path = self.subscriber.subscription_path(
            self.project_id, subscription_name
        )
        self.subscriber.acknowledge(
            request={"subscription": subscription_path, "ack_ids": ack_ids}
        )

    def pull_max_messages(self, subscription_name: str) -> list:
        """
        Pull 1000 messages from a subscription.

        Args:
            subscription_name (str): The name of the subscription.

        Returns:
            list: A list of received messages.

        """
        subscription_path = self.subscriber.subscription_path(
            self.project_id, subscription_name
        )
        response = self.subscriber.pull(
            request={"subscription": subscription_path, "max_messages": 1000}
        )
        return response.received_messages
