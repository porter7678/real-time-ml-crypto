import json
import os
from datetime import datetime, timezone

import joblib
from comet_ml.api import API
from loguru import logger
from pydantic import BaseModel

from src.config import CometConfig, HopsworksConfig, comet_config, hopsworks_config
from src.feature_engineering import add_technical_indicators, add_temporal_features
from src.hopsworks_api import push_value_to_feature_group
from src.model_registry import get_model_name
from src.ohlc_data_reader import OhlcDataReader
from src.preprocessing import keep_only_numeric_columns
from src.utils import timestamp_ms_to_human_readable_utc


class PricePrediction(BaseModel):
    price: float
    timestamp_ms: int
    product_id: str
    timestamp: str
    predicted_perc_change: float
    current_price: float

    def to_json(self) -> str:
        return json.dumps(self.model_dump())


class PricePredictor:

    def __init__(
        self,
        product_id: str,
        ohlc_window_sec: int,
        forecast_steps: int,
        feature_view_name: str,
        feature_view_version: int,
        last_n_minutes: int,
        features_to_use: list[str],
        model_path: str,
    ):
        self.product_id = product_id
        self.ohlc_window_sec = ohlc_window_sec
        self.forecast_steps = forecast_steps
        self.feature_view_name = feature_view_name
        self.feature_view_version = feature_view_version
        self.last_n_minutes = last_n_minutes
        self.features_to_use = features_to_use
        self.model_path = model_path

        logger.info(f"Loading model from {model_path}")
        self.model = self._load_model_from_disk(model_path)

        logger.info(
            f"Creating OHLC data reader and establishing connection to feature store"
        )
        self.ohlc_data_reader = OhlcDataReader(
            ohlc_window_sec=self.ohlc_window_sec,
            hopsworks_config=hopsworks_config,
            feature_view_name=self.feature_view_name,
            feature_view_version=self.feature_view_version,
        )

    def _load_model_from_disk(self, model_path: str):
        """Loads the model from the disk."""
        return joblib.load(model_path)

    @classmethod
    def from_model_registry(
        cls,
        product_id: str,
        ohlc_window_sec: int,
        forecast_steps: int,
        status: str,
    ):
        """
        Fetches the model artifact from the model registry, and all the relevant
        metadata we need to make predictions from this model artifact, and return a
        Predictor object.

        Steps:
        1. Load the model artifact from the model registry
        2. Fetch the relevant metadata from the model registry
        3. Return a Predictor object with the model artifact and the metadata

        Args:
            - product_id: the product_id of the model we want to fetch
            - ohlc_window_sec: the ohlc_window_sec of the model we want to fetch
            - forecast_steps: the forecast_steps of the model we want to fetch
            - status: the status of the model we want to fetch, for example "production"

        Returns:
            - Predictor: an instance of the Predictor class with the model artifact and
            the metadata fetched from the model registry
        """
        comet_api = API(api_key=comet_config.comet_api_key)

        # Step 1: Download the model artifact from the model registry
        model = comet_api.get_model(
            workspace=comet_config.comet_workspace,
            model_name=get_model_name(product_id, ohlc_window_sec, forecast_steps),
        )
        # find the version for the current model with the given `status`
        # Here I am assuming there is only one model version for that status.
        # I recommend you only have 1 production model at a time.
        # As for dev, or staging, you can have multiple versions, so we sort by
        # version and get the latest one.
        # Thanks Bilel for the suggestion!
        model_versions = model.find_versions(status=status)

        # sort the model versions list from high to low and pick the first element
        model_version = sorted(model_versions, reverse=True)[0]

        # download the model artifact for this `model_version`
        model.download(version=model_version, output_folder="./")
        model_path = (
            f"./{get_model_name(product_id, ohlc_window_sec, forecast_steps)}.joblib"
        )

        # Step 2: Fetch the relevant metadata from the model registry
        # find the experiment associated with this model
        experiment_key = model.get_details(version=model_version)["experimentKey"]

        # get the experiment
        experiment = comet_api.get_experiment_by_key(experiment_key)

        # get all the parameters I need from the experiment
        # - feature_view_name: str,
        # - feature_view_version: int,
        # - last_n_minutes: int,
        # - features_to_use: List[str],
        feature_view_name = experiment.get_parameters_summary("feature_view_name")[
            "valueCurrent"
        ]
        feature_view_version = int(
            experiment.get_parameters_summary("feature_view_version")["valueCurrent"]
        )
        last_n_minutes = int(
            experiment.get_parameters_summary("last_n_minutes")["valueCurrent"]
        )

        # features_to_use is a list of strings, so I need to parse the str that Comet ML returns
        features_to_use = json.loads(
            experiment.get_parameters_summary("feature_names")["valueCurrent"]
        )

        # Step 3: Return a Predictor object with the model artifact and the metadata
        return cls(
            model_path=model_path,
            product_id=product_id,
            ohlc_window_sec=ohlc_window_sec,
            forecast_steps=forecast_steps,
            feature_view_name=feature_view_name,
            feature_view_version=feature_view_version,
            last_n_minutes=last_n_minutes,
            features_to_use=features_to_use,
        )

    def predict(self) -> PricePrediction:
        """
        Fetches OHLCV candles from the online feature group, for the last `self.last_n_minutes` minutes,
        and makes a prediction for the next `self.forecast_steps` minutes.
        """
        # read the data from the online feature group
        ohlcv_data = self.ohlc_data_reader.read_from_online_store(
            product_id=self.product_id,
            last_n_minutes=self.last_n_minutes,
        )
        logger.debug(
            f"Read {len(ohlcv_data)} OHLCV candles from the online feature group"
        )

        # Preprocess the data and add necessary features
        logger.debug(f"Preprocessing the data and adding necessary features")
        ohlcv_data = keep_only_numeric_columns(ohlcv_data)
        ohlcv_data = add_technical_indicators(ohlcv_data)
        ohlcv_data = add_temporal_features(ohlcv_data)

        # double check the last row of the dataframe has no missing values
        logger.debug(f"Checking the last row of the dataframe has no missing values")
        # breakpoint()
        assert (
            ohlcv_data.iloc[-1].isna().sum() == 0
        ), "The last row of the dataframe has missing values"

        # extract the last row of ohlc_data into a new dataframe
        features = ohlcv_data.iloc[[-1]]

        # make a prediction
        predicted_price = self.model.predict(features)[0]

        # get the timestamp_ms that corresponds to the predicted_price
        predicted_timestamp_ms = (
            int(features["timestamp_ms"].values[0])
            + self.forecast_steps * self.ohlc_window_sec * 1000
        )

        # calculate the predicted percentage change
        predicted_perc_change = (
            predicted_price - features["close"].values[0]
        ) / features["close"].values[0]

        # build the response object
        prediction = PricePrediction(
            price=predicted_price,
            timestamp_ms=predicted_timestamp_ms,
            product_id=self.product_id,
            timestamp=timestamp_ms_to_human_readable_utc(predicted_timestamp_ms),
            predicted_perc_change=predicted_perc_change.round(6),
            current_price=features["close"].values[0],
        )

        return prediction


if __name__ == "__main__":

    predictor = PricePredictor.from_model_registry(
        product_id="BTC/USD",
        ohlc_window_sec=60,
        forecast_steps=5,
        status="production",
    )

    prediction = predictor.predict()
    logger.info(f"Prediction: {prediction.to_json()}")
    # logger.info(f"Prediction timestamp: {prediction.timestamp_ms_to_human_readable_utc()}")
