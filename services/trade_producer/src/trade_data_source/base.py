from abc import ABC, abstractmethod

from src.trade_data_source import Trade


class TradeSource(ABC):
    """
    Abstract base class for trade data sources.
    """

    @abstractmethod
    def get_trades(self) -> list[Trade]:
        """
        Retrieve the trades from the data source.

        Returns:
            A list of Trade objects.
        """
        pass

    @abstractmethod
    def is_done(self) -> bool:
        """
        Returns True if tehre are no more trades to retrieve, False otherwise.
        """
        pass
