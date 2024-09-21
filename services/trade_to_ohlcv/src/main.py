from datetime import timedelta

from loguru import logger
from quixstreams import Application


def init_ohlcv_candle(trade: dict) -> dict:
    """
    Returns the initial OHLCV candle when the first trade in that window is received.
    """
    return {
        "open": trade["price"],
        "high": trade["price"],
        "low": trade["price"],
        "close": trade["price"],
        "volume": trade["quantity"],
    }


def update_ohlcv_candle(candle: dict, trade: dict) -> dict:
    """
    Updates the OHLCV candle with the latest trade data.
    """
    candle["high"] = max(candle["high"], trade["price"])
    candle["low"] = min(candle["low"], trade["price"])
    candle["close"] = trade["price"]
    candle["volume"] += trade["quantity"]

    return candle


def transform_trade_to_ohlcv(
    kafka_broker_address: str,
    kafka_input_topic: str,
    kafka_output_topic: str,
    kafka_consumer_group_id: str,
    ohlcv_window_seconds: int,
):
    """
    Reads trades from the input Kafka topic, aggregates them into OHLCV data and saves
    them in the output Kafka topic.

    Args:
        kafka_broker_address: The address of the Kafka broker.
        kafka_input_topic: The name of the Kafka topic to read the trades.
        kafka_output_topic: The name of the Kafka topic to save the OHLCV data.
        kafka_consumer_group_id: The ID of the Kafka consumer group.

    Returns:
        None
    """
    # Create an Application instance with Kafka config
    app = Application(
        broker_address=kafka_broker_address, consumer_group=kafka_consumer_group_id
    )

    input_topic = app.topic(name=kafka_input_topic, value_deserializer="json")
    output_topic = app.topic(name=kafka_output_topic, value_serializer="json")

    # Create a Quixstream dataframe
    sdf = app.dataframe(input_topic)

    # sdf.update(logger.debug)

    # Create the 1-min candles
    sdf = (
        sdf.tumbling_window(duration_ms=timedelta(seconds=ohlcv_window_seconds))
        .reduce(initializer=init_ohlcv_candle, reducer=update_ohlcv_candle)
        .current()
    )

    sdf.update(logger.debug)

    sdf["open"] = sdf["value"]["open"]
    sdf["high"] = sdf["value"]["high"]
    sdf["low"] = sdf["value"]["low"]
    sdf["close"] = sdf["value"]["close"]
    sdf["volume"] = sdf["value"]["volume"]
    sdf["timestamp_ms"] = sdf["end"]

    # Keep only the necessary columns
    sdf = sdf[["timestamp_ms", "open", "high", "low", "close", "volume"]]

    # Push the OHLCV data to the output Kafka topic
    sdf = sdf.to_topic(output_topic)

    app.run(sdf)


if __name__ == "__main__":
    transform_trade_to_ohlcv(
        kafka_broker_address="localhost:19092",
        kafka_input_topic="trade",
        kafka_output_topic="ohlcv",
        kafka_consumer_group_id="consumer_group_trade_to_ohlcv",
        ohlcv_window_seconds=60,
    )
