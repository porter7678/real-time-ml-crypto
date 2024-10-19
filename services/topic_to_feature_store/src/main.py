import json

from loguru import logger
from quixstreams import Application

from src.hopsworks_api import HopsworksAPI


def topic_to_feature_store(
    kafka_broker_address: str,
    kafka_input_topic: str,
    kafka_consumer_group: str,
    feature_group_name: str,
    feature_group_version: int,
    feature_group_primary_keys: list[str],
    feature_group_event_time: str,
    start_offline_materialization: bool,
    batch_size: int,
):
    """
    Reads incoming messages from a Kafka topic and writes them to a feature store.

    Args:
        kafka_broker_address: The address of the Kafka broker.
        kafka_input_topic: The name of the Kafka topic to read from.
        kafka_consumer_group: The name of the Kafka consumer group.
        feature_group_name: The name of the feature group.
        feature_group_version: The version of the feature group.
        feature_group_primary_keys: The primary keys of the feature group.
        feature_group_event_time: The event time of the feature group.
        start_offline_materialization: Whether to start the offline materialization
        batch_size: The number of messages to accumulate in memory before pushing
            to the feature store.

    Returns:
        None
    """
    app = Application(
        broker_address=kafka_broker_address,
        consumer_group=kafka_consumer_group,
    )
    input_topic = app.topic(kafka_input_topic)
    hopsworks_api = HopsworksAPI()

    batch = []
    with app.get_consumer() as consumer:

        # Using the input_topic object keeps this consistent when we deploy to Quix
        consumer.subscribe(topics=[input_topic.name])

        while True:
            msg = consumer.poll(0.1)
            if msg is None:
                continue
            elif msg.error():
                logger.error(f"Kafka error: {msg.error()}")
                continue

            value = msg.value()

            # decode the message bytes into a dict
            value = json.loads(value.decode("utf-8"))

            # Append the message to the batch
            batch.append(value)

            # If the batch is not full, continue
            # TODO: Make sure the last batch gets pushed even if not full
            if len(batch) < batch_size:
                logger.debug(f"Batch size: {len(batch)} < {batch_size}. Continuing...")
                continue

            logger.debug(
                f"Batch size: {len(batch)} >= {batch_size}. Pushing to feature store..."
            )
            if batch_size == 1:
                logger.debug(f"Batch: {batch}")
            hopsworks_api.push_value_to_feature_group(
                batch,
                feature_group_name,
                feature_group_version,
                feature_group_primary_keys,
                feature_group_event_time,
                start_offline_materialization,
            )

            # Clear the batch
            batch = []


if __name__ == "__main__":
    from src.config import config

    topic_to_feature_store(
        kafka_broker_address=config.kafka_broker_address,
        kafka_input_topic=config.kafka_input_topic,
        kafka_consumer_group=config.kafka_consumer_group,
        feature_group_name=config.feature_group_name,
        feature_group_version=config.feature_group_version,
        feature_group_primary_keys=config.feature_group_primary_keys,
        feature_group_event_time=config.feature_group_event_time,
        start_offline_materialization=config.start_offline_materialization,
        batch_size=config.batch_size,
    )
