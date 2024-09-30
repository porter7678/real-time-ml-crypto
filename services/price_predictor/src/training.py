from loguru import logger
from sklearn.metrics import mean_absolute_error
from src.config import HopsworksConfig
from src.models.current_price_baseline import CurrentPriceBaseline
from src.ohlcv_data_reader import OhlcDataReader


def train_model(
    hopsworks_config: HopsworksConfig,
    feature_view_name: str,
    feature_view_version: int,
    feature_group_name: str,
    feature_group_version: int,
    ohlcv_window_sec: int,
    product_id: str,
    last_n_days: int,
    forecast_steps: int,
    perc_test_data: float = 0.3,
):
    """
    Reads features from the feature store
    Trains a model
    Saves the model to the model registry

    Args:
        hopsworks_config: The configuration for Hopsworks.
        feature_view_name: The name of the feature view.
        feature_view_version: The version of the feature view.
        feature_group_name: The name of the feature group.
        feature_group_version: The version of the feature group.
        ohlcv_window_sec: The window size of the OHLCV data.
        product_id: The product ID.
        last_n_days: The number of days to look back.
        forecast_steps: The number of steps to forecast.
        perc_test_data: The percentage of data to use for testing

    Returns:
        None
    """
    # Load (sorted) feature data from the feature store
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
    logger.debug(f"Loaded {len(ohlcv_data)} rows of data")

    # Split the data into training and testing sets
    test_size = int(len(ohlcv_data) * perc_test_data)
    train_df = ohlcv_data[:-test_size]
    test_df = ohlcv_data[-test_size:]

    # Create my target column (future price)
    train_df["target_price"] = train_df["close"].shift(-forecast_steps)
    test_df["target_price"] = test_df["close"].shift(-forecast_steps)

    # Remove rows with NaN values
    train_df = train_df.dropna()
    test_df = test_df.dropna()
    logger.debug(f"Train size: {len(train_df)}, Test size: {len(test_df)}")

    # Split data into features and target
    X_train = train_df.drop(columns=["target_price"])
    y_train = train_df["target_price"]
    X_test = test_df.drop(columns=["target_price"])
    y_test = test_df["target_price"]

    # Log dimensions of the data
    logger.debug(f"X_train shape: {X_train.shape}")
    logger.debug(f"y_train shape: {y_train.shape}")
    logger.debug(f"X_test shape: {X_test.shape}")
    logger.debug(f"y_test shape: {y_test.shape}")

    # Train a model
    model = CurrentPriceBaseline()
    model.fit(X_train, y_train)

    # Evaluate the model
    y_pred = model.predict(X_test)
    mae = mean_absolute_error(y_test, y_pred)
    logger.info(f"Mean absolute error: {mae:.2f}")

    # Save the model to the model registry


if __name__ == "__main__":

    from src.config import config, hopsworks_config

    train_model(
        hopsworks_config=hopsworks_config,
        feature_view_name=config.feature_view_name,
        feature_view_version=config.feature_view_version,
        feature_group_name=config.feature_group_name,
        feature_group_version=config.feature_group_version,
        ohlcv_window_sec=config.ohlcv_window_sec,
        product_id=config.product_id,
        last_n_days=config.last_n_days,
        forecast_steps=config.forecast_steps,
    )
