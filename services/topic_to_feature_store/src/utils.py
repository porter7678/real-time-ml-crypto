from datetime import datetime, timezone

from src.logger import logger


def log_ohlcv_to_elasticsearch(value: dict):
    """
    Logs the OHLCV data to Elasticsearch.

    Args:
        value (dict): The OHLCV data

    Returns:
        None
    """
    logger.debug(f'Timestamp from the value dictionary: {value["timestamp_ms"]}')
    timestamp = datetime.fromtimestamp(value["timestamp_ms"] / 1000.0, tz=timezone.utc)
    logger.bind(
        timestamp=timestamp.isoformat(),
        product_id=value["product_id"],
        price=value["close"],
    ).info(f"Received candle: {value}")
