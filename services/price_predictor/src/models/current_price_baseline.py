import pandas as pd


class CurrentPriceBaseline:

    def __init__(self):
        pass

    def fit(self, X: pd.DataFrame, y: pd.Series):
        pass

    def predict(self, X: pd.DataFrame) -> pd.Series:
        """
        Predict the future price based on the current price
        """
        return X["close"]
