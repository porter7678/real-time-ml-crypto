from pydantic_settings import BaseSettings


class Config(BaseSettings):
    model_config = {"env_file": ".env"}

    kafka_broker_address: str
    kafka_topic: str
    product_id: str

    live_or_historical: str | None = None
    last_n_days: int | None = None


config = Config()
