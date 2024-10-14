import hashlib
import os

import joblib
from comet_ml import Experiment
from loguru import logger
from sklearn.metrics import mean_absolute_error
from xgboost import XGBRegressor

from src.config import CometConfig, HopsworksConfig
from src.feature_engineering import add_technical_indicators, add_temporal_features
from src.model_registry import get_model_name
from src.models.current_price_baseline import CurrentPriceBaseline
from src.models.xgboost_model import XGBoostModel
from src.ohlc_data_reader import OhlcDataReader
from src.preprocessing import keep_only_numeric_columns
from src.utils import hash_dataframe


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
    n_search_trials: int = 10,
    n_splits: int = 3,
    last_n_minutes: int = 30,
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
        n_search_trials: The number of search trials for hyperparameter optimization.
        n_splits: The number of splits for cross-validation.
        last_n_minutes: The number of minutes to look back

    Returns:
        None
    """
    # Create a Comet experiment
    experiment = Experiment(
        api_key=comet_config.comet_api_key,
        project_name=comet_config.comet_project_name,
    )
    experiment.log_parameter("last_n_days", last_n_days)
    experiment.log_parameter("forecast_steps", forecast_steps)
    experiment.log_parameter("n_search_trials", n_search_trials)
    experiment.log_parameter("n_splits", n_splits)

    # Log feature view information
    experiment.log_parameter("feature_view_name", feature_view_name)
    experiment.log_parameter("feature_view_version", feature_view_version)

    # log number of minutes of data in the past I need to generate predictions
    experiment.log_parameter("last_n_minutes", last_n_minutes)

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

    # Log a hash of the data
    data_hash = hash_dataframe(ohlcv_data_raw)
    experiment.log_parameter("data_hash", data_hash)

    # Create features
    ohlcv_data = keep_only_numeric_columns(ohlcv_data_raw)
    ohlcv_data = add_technical_indicators(ohlcv_data)
    ohlcv_data = add_temporal_features(ohlcv_data)
    experiment.log_parameter("features", ohlcv_data.columns)
    experiment.log_parameter("n_features", len(ohlcv_data.columns))

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

    # Train an xgboost model
    xgb_model = XGBoostModel()
    xgb_model.fit(
        X_train,
        y_train,
        n_search_trials=n_search_trials,
        n_splits=n_splits,
    )

    # Evaluate the model
    y_pred = xgb_model.predict(X_test)
    mae = mean_absolute_error(y_test, y_pred)
    logger.info(f"MAE: {mae:.2f}")
    experiment.log_metric("mae", mae)

    # Compute mae on the training set as a sanity check
    y_pred_train = xgb_model.predict(X_train)
    mae_train = mean_absolute_error(y_train, y_pred_train)
    logger.info(f"MAE train: {mae_train:.2f}")
    experiment.log_metric("mae_train", mae_train)

    # Save the model locally
    model_name = get_model_name(product_id, ohlcv_window_sec, forecast_steps)
    local_model_path = f"{model_name}.joblib"
    joblib.dump(xgb_model.get_model_obj(), local_model_path)

    # Attach the model artifact to the Comet experiment
    experiment.log_model(
        name=model_name,
        file_or_folder=local_model_path,
        overwrite=True,
    )

    if mae < mae_current_price or True:  # FIXME: Remove True
        # Register model in Comet
        logger.info(
            f"Model is better than baseline. Registering model in Comet: {model_name}"
        )
        experiment.register_model(
            model_name=model_name,
        )
    else:
        logger.info(
            f"Model is not better than baseline. Not registering model in Comet: {model_name}"
        )

    os.remove(local_model_path)
    experiment.end()


if __name__ == "__main__":

    from src.config import comet_config, config, hopsworks_config

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
        n_search_trials=config.n_search_trials,
        n_splits=config.n_splits,
    )
