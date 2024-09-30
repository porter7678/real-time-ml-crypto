from src.config import HopsworksConfig
from src.ohlcv_data_reader import OhlcDataReader


def train_model(
    feature_view_name: str,
    feature_view_version: int,
    feature_group_name: str,
    feature_group_version: int,
    ohlcv_window_sec: int,
    product_id: str,
    last_n_days: int,
    hopsworks_config: HopsworksConfig,
):
    """
    Reads features from the feature store
    Trains a model
    Saves the model to the model registry
    """
    # Load feature data from the feature store
    ohlcv_data_reader = OhlcDataReader(
        ohlc_window_sec=ohlcv_window_sec,
        hopsworks_config=hopsworks_config,
        feature_view_name=feature_view_name,
        feature_view_version=feature_view_version,
        feature_group_name=feature_group_name,
        feature_group_version=feature_group_version,
    )

    ohlcv_data = ohlcv_data_reader.read_from_offline_store(
        product_id=product_id,
        last_n_days=last_n_days,
    )

    breakpoint()

    # Train a model

    # Save the model to the model registry


if __name__ == "__main__":

    from src.config import config, hopsworks_config

    train_model(
        feature_view_name=config.feature_view_name,
        feature_view_version=config.feature_view_version,
        feature_group_name=config.feature_group_name,
        feature_group_version=config.feature_group_version,
        ohlcv_window_sec=config.ohlcv_window_sec,
        product_id=config.product_id,
        last_n_days=config.last_n_days,
        hopsworks_config=hopsworks_config,
    )
