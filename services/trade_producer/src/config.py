from pydantic_settings import BaseSettings


class Config(BaseSettings):
    model_config = {"env_file": ".env"}

    kafka_broker_address: str
    kafka_topic: str
    product_id: str


config = Config()
