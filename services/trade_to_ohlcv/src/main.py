from datetime import timedelta
from typing import Any, List, Optional, Tuple

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
        "product_id": trade["product_id"],
    }


def update_ohlcv_candle(candle: dict, trade: dict) -> dict:
    """
    Updates the OHLCV candle with the latest trade data.
    """
    candle["high"] = max(candle["high"], trade["price"])
    candle["low"] = min(candle["low"], trade["price"])
    candle["close"] = trade["price"]
    candle["volume"] += trade["quantity"]
    candle["product_id"] = trade["product_id"]

    return candle


def custom_ts_extractor(
    value: Any,
    headers: Optional[List[Tuple[str, bytes]]],
    timestamp: float,
    timestamp_type,
) -> int:
    """
    Specify a custom timestamp extractor to extract the timestamp from the trade data
    rather than from Kafka timestamp.
    """
    return value["timestamp_ms"]


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

    input_topic = app.topic(
        name=kafka_input_topic,
        value_deserializer="json",
        timestamp_extractor=custom_ts_extractor,
    )
    output_topic = app.topic(name=kafka_output_topic, value_serializer="json")

    # Create a Quixstream dataframe
    sdf = app.dataframe(input_topic)

    # sdf.update(logger.debug)

    # Create the 1-min candles
    sdf = (
        sdf.tumbling_window(duration_ms=timedelta(seconds=ohlcv_window_seconds)).reduce(
            initializer=init_ohlcv_candle, reducer=update_ohlcv_candle
        )
        # .current()
        .final()
    )

    sdf.update(logger.debug)

    sdf["open"] = sdf["value"]["open"]
    sdf["high"] = sdf["value"]["high"]
    sdf["low"] = sdf["value"]["low"]
    sdf["close"] = sdf["value"]["close"]
    sdf["volume"] = sdf["value"]["volume"]
    sdf["product_id"] = sdf["value"]["product_id"]
    sdf["timestamp_ms"] = sdf["end"]

    # Keep only the necessary columns
    sdf = sdf[["product_id", "timestamp_ms", "open", "high", "low", "close", "volume"]]

    # Push the OHLCV data to the output Kafka topic
    sdf = sdf.to_topic(output_topic)

    app.run(sdf)


if __name__ == "__main__":
    from src.config import config

    transform_trade_to_ohlcv(
        kafka_broker_address=config.kafka_broker_address,
        kafka_input_topic=config.kafka_input_topic,
        kafka_output_topic=config.kafka_output_topic,
        kafka_consumer_group_id=config.kafka_consumer_group,
        ohlcv_window_seconds=config.ohlcv_window_seconds,
    )
