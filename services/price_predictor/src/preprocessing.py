from datetime import datetime, timezone

from loguru import logger
import pandas as pd


def keep_only_numeric_columns(df: pd.DataFrame) -> pd.DataFrame:
    """
    Keep only the numeric columns from the OHLCV data we read from
    the feature store.
    """
    return df[["open", "high", "low", "close", "volume", "timestamp_ms"]]


def get_and_check_most_recent_row(df: pd.DataFrame) -> pd.DataFrame:
    """
    Extract the last row of the OHLCV data and check that it is recent enough and
    not missing data.
    """
    # extract the last row of ohlcv_data
    most_recent_row = df.iloc[[-1]]

    # Check that the last row is within the last 3 minutes
    # This is to make sure that the data is fresh
    final_timestamp_ms = most_recent_row["timestamp_ms"].values[0]
    current_timestamp_ms = datetime.now(timezone.utc).timestamp() * 1000
    if current_timestamp_ms - final_timestamp_ms > 60 * 1000 * 3:
        logger.warning("The most recent row of the dataframe is older than 3 minutes")

    # Log how many minutes ago the last row was
    minutes_ago = (current_timestamp_ms - final_timestamp_ms) / 1000 / 60
    logger.debug(f"The last row of the dataframe is {minutes_ago:.2f} minutes old")

    # Check the last row of the dataframe has no missing values
    if most_recent_row.isna().sum().sum() > 0:
        logger.debug(most_recent_row.transpose())
        raise ValueError("The last row of the dataframe has missing values")

    return most_recent_row
