from loguru import logger
from elasticsearch import Elasticsearch
import json

from src.config import elasticsearch_config as config

# config.elasticsearch_url = 'http://localhost:9200'


def elasticsearch_sink(message):
    """ "
    This function is used to log messages to Elasticsearch.

    Args:
        message (Message): The message to log.

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
        "message": record["message"],
        "service": "price_predictor_api",
        "module": record["name"],
        "function": record["function"],
        "line": record["line"],
        "process": record["process"].name,
        "thread": record["thread"].name,
        "exception": record["exception"],
        # Extract the extra parameters
        "timestamp_prediction": record["extra"].get("timestamp"),
        "product_id": record["extra"].get("product_id"),
        "price_prediction": record["extra"].get("price"),
    }

    # print(log_entry)

    # Send log to Elasticsearch
    # TODO: this index is not correct
    es.index(
        index="feature_pipeline-topic_to_feature_store", body=json.dumps(log_entry)
    )


# Configure Loguru to use the Elasticsearch sink
logger.add(elasticsearch_sink, level="INFO")
