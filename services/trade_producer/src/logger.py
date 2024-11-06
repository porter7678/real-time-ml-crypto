from loguru import logger
from elasticsearch import Elasticsearch
import json

from src.config import elasticsearch_config as config


def elasticsearch_sink(message):
    """ "
    This function is used to log messages to Elasticsearch.

    Args:
        message (str): The message to log.

    Returns:
        None
    """
    # Initialize Elasticsearch client
    es = Elasticsearch([config.elasticsearch_url])

    # Extract log details
    record = message.record
    log_entry = {
        "timestamp": record["time"].isoformat(),
        "level": record["level"].name,
        "service": "trade_producer",
        "message": record["message"],
        "module": record["name"],
        "function": record["function"],
        "line": record["line"],
        "process": record["process"].name,
        "thread": record["thread"].name,
        "exception": record["exception"],
    }

    # Send log to Elasticsearch
    es.index(index="feature_pipeline-trade_producer", body=json.dumps(log_entry))


# Configure Loguru to use the Elasticsearch sink
logger.add(elasticsearch_sink, level="INFO")
