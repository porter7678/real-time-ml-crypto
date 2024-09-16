from loguru import logger
from quixstreams import Application

from src.kraken_websocket_api import KrakenWebsocketAPI, Trade


def produce_trades(
    kafka_broker_address: str,
    kafka_topic: str,
    product_id: str,
):
    """
    Reads trades from the Kraken websocket API and saves them in the given Kafka topic.

    Args:
        kafka_broker_address: The address of the Kafka broker.
        kafka_topic: The name of the Kafka topic to save the trades.
        product_id: The product ID to fetch trades from the Kraken API.

    Returns:
        None
    """
    # Create an Application instance with Kafka config
    app = Application(broker_address=kafka_broker_address)
    # Define a topic "my_topic" with JSON serialization
    topic = app.topic(name=kafka_topic, value_serializer="json")

    # Create a KrakenWebsocketAPI instance
    kraken_api = KrakenWebsocketAPI(product_id=product_id)

    # Create a Producer instance
    with app.get_producer() as producer:

        while True:
            # Sample event data
            # event = {"id": "1", "text": "Lorem ipsum dolor sit amet"}

            trades: list[Trade] = kraken_api.get_trades()

            for trade in trades:
                # Serialize the event using the defined Topic
                message = topic.serialize(
                    key=trade.product_id, value=trade.model_dump()
                )
                # Produce the message into the Kafka topic
                producer.produce(topic=topic.name, value=message.value, key=message.key)

                logger.debug(f"Pushed trade to Kafka: {trade}")


if __name__ == "__main__":
    # Call the function with the given arguments
    produce_trades(
        kafka_broker_address="localhost:19092",
        kafka_topic="trade",
        product_id="BTC/USD",
    )
