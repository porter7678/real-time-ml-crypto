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
    forecast_steps: int


class HopsworksConfig(BaseSettings):
    model_config = {"env_file": "hopsworks.credentials.env"}

    hopsworks_project_name: str
    hopsworks_api_key: str


class CometConfig(BaseSettings):
    model_config = {"env_file": "comet.credentials.env"}

    comet_api_key: str
    comet_project_name: str


config = Config()
hopsworks_config = HopsworksConfig()
comet_config = CometConfig()
