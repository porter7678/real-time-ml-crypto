import pandas as pd


def keep_only_numeric_columns(df: pd.DataFrame) -> pd.DataFrame:
    """
    Keep only the numeric columns from the OHLCV data we read from
    the feature store.
    """
    return df[["open", "high", "low", "close", "volume", "timestamp_ms"]]
