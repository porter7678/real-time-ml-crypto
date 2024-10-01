from loguru import logger
from comet_ml import Experiment
from sklearn.metrics import mean_absolute_error
from xgboost import XGBRegressor

from src.config import HopsworksConfig, CometConfig
from src.feature_engineering import add_technical_indicators
from src.models.current_price_baseline import CurrentPriceBaseline
from src.ohlcv_data_reader import OhlcDataReader


def train_model(
    comet_config: CometConfig,
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
        comet_config: The configuration for Comet.
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
    # Create a Comet experiment
    experiment = Experiment(
        api_key=comet_config.comet_api_key,
        project_name=comet_config.comet_project_name,
    )

    # Load (sorted) feature data from the feature store
    ohlcv_data_reader = OhlcDataReader(
        ohlc_window_sec=ohlcv_window_sec,
        hopsworks_config=hopsworks_config,
        feature_view_name=feature_view_name,
        feature_view_version=feature_view_version,
        feature_group_name=feature_group_name,
        feature_group_version=feature_group_version,
    )

    ohlcv_data_raw = ohlcv_data_reader.read_from_offline_store(
        product_id=product_id,
        last_n_days=last_n_days,
    )
    logger.debug(f"Loaded {len(ohlcv_data_raw)} rows of data")
    experiment.log_parameter("data_size", len(ohlcv_data_raw))

    # Create features
    ohlcv_data = ohlcv_data_raw[["open", "high", "low", "close", "volume"]]
    ohlcv_data = add_technical_indicators(ohlcv_data)

    # Create target
    ohlcv_data.loc[:, "target_price"] = ohlcv_data["close"].shift(-forecast_steps)

    # Drop rows with NaN values
    n_rows_before = len(ohlcv_data)
    ohlcv_data = ohlcv_data.dropna()
    n_rows_after = len(ohlcv_data)
    logger.debug(f"Dropped {n_rows_before - n_rows_after} rows with NaN values")

    # Split the data into training and testing sets
    test_size = int(len(ohlcv_data) * perc_test_data)
    train_df = ohlcv_data[:-test_size]
    test_df = ohlcv_data[-test_size:]
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
    experiment.log_parameter("X_train_shape", X_train.shape)
    experiment.log_parameter("y_train_shape", y_train.shape)
    experiment.log_parameter("X_test_shape", X_test.shape)
    experiment.log_parameter("y_test_shape", y_test.shape)

    # Build a baseline model
    current_price_model = CurrentPriceBaseline()
    current_price_model.fit(X_train, y_train)

    # Evaluate the model
    y_pred_current_price = current_price_model.predict(X_test)
    mae_current_price = mean_absolute_error(y_test, y_pred_current_price)
    logger.info(f"MAE baseline: {mae_current_price:.2f}")
    experiment.log_metric("mae_current_price_baseline", mae_current_price)

    # Compute mae on the training set as a sanity check
    y_pred_train = current_price_model.predict(X_train)
    mae_train = mean_absolute_error(y_train, y_pred_train)
    logger.info(f"MAE train: {mae_train:.2f}")
    experiment.log_metric("mae_train", mae_train)

    # Train an xgboost model
    xgb_model = XGBRegressor()
    xgb_model.fit(X_train, y_train)
    y_pred = xgb_model.predict(X_test)
    mae = mean_absolute_error(y_test, y_pred)
    logger.info(f"MAE: {mae:.2f}")
    experiment.log_metric("mae", mae)

    # Save the model to the model registry
    experiment.end()


if __name__ == "__main__":

    from src.config import config, hopsworks_config, comet_config

    train_model(
        comet_config=comet_config,
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
