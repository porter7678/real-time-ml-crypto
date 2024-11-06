from pydantic_settings import BaseSettings


class Config(BaseSettings):
    model_config = {"env_file": ".env"}

    kafka_broker_address: str | None = None
    kafka_topic: str
    product_ids: list[str]

    live_or_historical: str | None = None
    last_n_days: int | None = None


class ElasticSearchConfig(BaseSettings):
    model_config = {"env_file": "elastic_search.env"}

    elasticsearch_url: str


config = Config()
elasticsearch_config = ElasticSearchConfig()
