import pandas as pd


def hash_dataframe(df: pd.DataFrame) -> str:
    """Function to create a consistent hash of a pandas DataFrame."""
    return pd.util.hash_pandas_object(df).sum()
