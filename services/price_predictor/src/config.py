from pydantic_settings import BaseSettings


class Config(BaseSettings):
    model_config = {"env_file": ".env"}

    feature_view_name: str
    feature_view_version: int
    feature_group_name: str
    feature_group_version: int
    ohlcv_window_sec: int
    product_id: str
    last_n_days: int


class HopsworksConfig(BaseSettings):
    model_config = {"env_file": "credentials.env"}

    hopsworks_project_name: str
    hopsworks_api_key: str


config = Config()
hopsworks_config = HopsworksConfig()
