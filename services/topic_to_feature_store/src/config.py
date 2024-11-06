from pydantic_settings import BaseSettings


class Config(BaseSettings):
    model_config = {"env_file": ".env"}

    kafka_broker_address: str | None = None
    kafka_input_topic: str
    kafka_consumer_group: str

    feature_group_name: str
    feature_group_version: int
    feature_group_primary_keys: list[str]
    feature_group_event_time: str
    start_offline_materialization: bool
    batch_size: int = 1


class HopsworksConfig(BaseSettings):
    model_config = {"env_file": "credentials.env"}

    hopsworks_project_name: str
    hopsworks_api_key: str


class ElasticSearchConfig(BaseSettings):
    model_config = {"env_file": "elastic_search.env"}

    elasticsearch_url: str


config = Config()
hopsworks_config = HopsworksConfig()
elasticsearch_config = ElasticSearchConfig()
