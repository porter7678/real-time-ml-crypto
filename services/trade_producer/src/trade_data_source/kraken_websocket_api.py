import json
from datetime import datetime, timezone

from loguru import logger
from websocket import create_connection

from src.trade_data_source.base import Trade, TradeSource


class KrakenWebsocketAPI(TradeSource):
    """
    Class for reading real-time trades from the Kraken websocket API.
    """

    URL = "wss://ws.kraken.com/v2"

    def __init__(self, product_ids: list[str]):
        """
        Initializes the KrakenWebsocketAPI instance with the given product ID.

        Args:
            product_id: The product ID to fetch trades from the Kraken API.
        """
        self.product_ids = product_ids

        # Create a websocket connection
        self._ws = create_connection(self.URL)
        logger.debug("Connection established")

        # Subscribe to trades for a given product ID
        self._subscribe(product_ids)

    def get_trades(self) -> list[Trade]:
        """
        Returns the latest batch of trades from the Kraken API.

        Returns:
            A list of Trade objects.
        """
        message = self._ws.recv()

        if "heartbeat" in message:
            logger.debug("Heartbeat received")
            return []

        message = json.loads(message)

        # Extract the trade data
        trades = []
        for trade in message["data"]:
            trades.append(
                Trade(
                    product_id=trade["symbol"],
                    quantity=trade["price"],
                    price=trade["qty"],
                    timestamp_ms=self.to_ms(trade["timestamp"]),
                )
            )

        return trades

    def is_done(self) -> bool:
        """
        Returns True if the API connection is closed.
        """
        return False

    def _subscribe(self, product_ids: list[str]):
        """
        Subscribes to the trades for the given product IDs.

        Args:
            product_id: The product ID to subscribe to.
        """
        logger.debug(f"Subscribing to trades for {product_ids}")
        msg = {
            "method": "subscribe",
            "params": {"channel": "trade", "symbol": product_ids, "snapshot": False},
        }
        self._ws.send(json.dumps(msg))
        logger.debug(f"Subscription successful!")

        # Discard the first two messages, because they are just confirmations
        for product_id in product_ids:
            _ = self._ws.recv()
            _ = self._ws.recv()

    @staticmethod
    def to_ms(timestamp: str) -> int:
        """
        A function that transforms a timestamps expressed
        as a string like this '2024-06-17T09:36:39.467866Z'
        into a timestamp expressed in milliseconds.

        Args:
            timestamp: A timestamp string.

        Returns:
            The timestamp in milliseconds.
        """
        timestamp = datetime.fromisoformat(timestamp[:-1]).replace(tzinfo=timezone.utc)
        return int(timestamp.timestamp() * 1000)
