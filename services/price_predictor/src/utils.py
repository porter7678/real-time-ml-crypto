from datetime import datetime, timezone

import pandas as pd


# Function to create a consistent hash of a pandas DataFrame
def hash_dataframe(df: pd.DataFrame) -> str:
    return pd.util.hash_pandas_object(df).sum()


def timestamp_ms_to_human_readable_utc(timestamp_ms: int) -> str:
    """
    Convert a timestamp in milliseconds to a human-readable UTC datetime string.

    Args:
        timestamp_ms (int): The timestamp in milliseconds.

    Returns:
        str: A human-readable UTC datetime string.
    """
    utc_datetime = datetime.fromtimestamp(timestamp_ms / 1000, tz=timezone.utc)
    return utc_datetime.strftime("%Y-%m-%d %H:%M:%S UTC")
