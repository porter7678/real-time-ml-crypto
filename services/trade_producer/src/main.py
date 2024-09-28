from loguru import logger
from quixstreams import Application

from src.trade_data_source import Trade, TradeSource


def produce_trades(
    kafka_broker_address: str,
    kafka_topic: str,
    trade_data_source: TradeSource,
):
    """
    Reads trades from the Kraken websocket API and saves them in the given Kafka topic.

    Args:
        kafka_broker_address: The address of the Kafka broker.
        kafka_topic: The name of the Kafka topic to save the trades.
        trade_data_source: The data source to get the trades from.

    Returns:
        None
    """
    # Create an Application instance with Kafka config
    app = Application(broker_address=kafka_broker_address)
    topic = app.topic(name=kafka_topic, value_serializer="json")

    # Create a Producer instance
    with app.get_producer() as producer:

        while not trade_data_source.is_done():
            trades: list[Trade] = trade_data_source.get_trades()

            for trade in trades:
                # Serialize the event using the defined Topic
                message = topic.serialize(
                    key=trade.product_id, value=trade.model_dump()
                )
                # Produce the message into the Kafka topic
                producer.produce(topic=topic.name, value=message.value, key=message.key)

                logger.debug(f"Pushed trade to Kafka: {trade}")


if __name__ == "__main__":
    from src.config import config
    from src.trade_data_source import KrakenWebsocketAPI

    kraken_api = KrakenWebsocketAPI(product_id=config.product_id)

    produce_trades(
        kafka_broker_address=config.kafka_broker_address,
        kafka_topic=config.kafka_topic,
        trade_data_source=kraken_api,
    )
