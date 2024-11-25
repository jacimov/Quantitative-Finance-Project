"""Paper trading implementation for Alpaca and Oanda brokers."""

import logging
import os
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Union

import alpaca_trade_api as tradeapi
from oandapyV20 import API
import oandapyV20.endpoints.orders as orders
import oandapyV20.endpoints.positions as positions

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class PaperTrader(ABC):
    """Abstract base class for paper trading implementations."""

    @abstractmethod
    def place_order(
        self,
        symbol: str,
        qty: float,
        side: str,
        order_type: str = 'market',
        limit_price: Optional[float] = None
    ) -> Dict:
        """Place a trading order.

        Args:
            symbol: Trading symbol (e.g., 'AAPL' or 'EUR_USD')
            qty: Order quantity
            side: 'buy' or 'sell'
            order_type: 'market' or 'limit'
            limit_price: Required if order_type is 'limit'

        Returns:
            Dict containing order details
        """
        pass

    @abstractmethod
    def get_positions(self) -> List[Dict]:
        """Get current positions.

        Returns:
            List of dictionaries containing position details
        """
        pass

    @abstractmethod
    def close_position(self, symbol: str) -> Dict:
        """Close a specific position.

        Args:
            symbol: Trading symbol to close position for

        Returns:
            Dict containing closure details
        """
        pass


class AlpacaPaperTrader(PaperTrader):
    """Alpaca paper trading implementation."""

    def __init__(self, api_key: str, api_secret: str):
        """Initialize Alpaca paper trading client.

        Args:
            api_key: Alpaca API key
            api_secret: Alpaca API secret
        """
        self.api = tradeapi.REST(
            api_key,
            api_secret,
            base_url='https://paper-api.alpaca.markets'
        )
        logger.info("Initialized Alpaca paper trading client")

    def place_order(
        self,
        symbol: str,
        qty: float,
        side: str,
        order_type: str = 'market',
        limit_price: Optional[float] = None
    ) -> Dict:
        """Place an order with Alpaca.

        Args:
            symbol: Trading symbol (e.g., 'AAPL')
            qty: Order quantity
            side: 'buy' or 'sell'
            order_type: 'market' or 'limit'
            limit_price: Required if order_type is 'limit'

        Returns:
            Dict containing order details

        Raises:
            Exception: If order placement fails
        """
        try:
            order = self.api.submit_order(
                symbol=symbol,
                qty=qty,
                side=side,
                type=order_type,
                limit_price=limit_price,
                time_in_force='gtc'
            )
            logger.info(f"Placed {side} order for {qty} {symbol}")
            return order._raw
        except Exception as e:
            logger.error(f"Error placing order: {str(e)}")
            raise

    def get_positions(self) -> List[Dict]:
        """Get all open positions.

        Returns:
            List of dictionaries containing position details

        Raises:
            Exception: If unable to fetch positions
        """
        try:
            positions = self.api.list_positions()
            return [pos._raw for pos in positions]
        except Exception as e:
            logger.error(f"Error getting positions: {str(e)}")
            raise

    def close_position(self, symbol: str) -> Dict:
        """Close a position for a specific symbol.

        Args:
            symbol: Trading symbol to close position for

        Returns:
            Dict containing closure details

        Raises:
            Exception: If position closure fails
        """
        try:
            response = self.api.close_position(symbol)
            logger.info(f"Closed position for {symbol}")
            return response._raw
        except Exception as e:
            logger.error(f"Error closing position: {str(e)}")
            raise


class OandaPaperTrader(PaperTrader):
    """Oanda paper trading implementation."""

    def __init__(self, access_token: str, account_id: str):
        """Initialize Oanda paper trading client.

        Args:
            access_token: Oanda API access token
            account_id: Oanda account ID
        """
        self.api = API(access_token=access_token, environment="practice")
        self.account_id = account_id
        logger.info("Initialized Oanda paper trading client")

    def place_order(
        self,
        symbol: str,
        qty: float,
        side: str,
        order_type: str = 'market',
        limit_price: Optional[float] = None
    ) -> Dict:
        """Place an order with Oanda.

        Args:
            symbol: Trading symbol (e.g., 'EUR_USD')
            qty: Order quantity (units)
            side: 'buy' or 'sell'
            order_type: 'market' or 'limit'
            limit_price: Required if order_type is 'limit'

        Returns:
            Dict containing order details

        Raises:
            Exception: If order placement fails
        """
        try:
            units = qty if side == 'buy' else -qty
            order_data = {
                "order": {
                    "units": str(units),
                    "instrument": symbol,
                    "timeInForce": "GTC",
                    "type": order_type.upper(),
                    "positionFill": "DEFAULT"
                }
            }

            if order_type == 'limit' and limit_price is not None:
                order_data["order"]["price"] = str(limit_price)

            r = orders.OrderCreate(self.account_id, data=order_data)
            response = self.api.request(r)
            logger.info(f"Placed {side} order for {abs(units)} {symbol}")
            return response

        except Exception as e:
            logger.error(f"Error placing order: {str(e)}")
            raise

    def get_positions(self) -> List[Dict]:
        """Get all open positions.

        Returns:
            List of dictionaries containing position details

        Raises:
            Exception: If unable to fetch positions
        """
        try:
            r = positions.OpenPositions(accountID=self.account_id)
            response = self.api.request(r)
            return response['positions']
        except Exception as e:
            logger.error(f"Error getting positions: {str(e)}")
            raise

    def close_position(self, symbol: str) -> Dict:
        """Close a position for a specific symbol.

        Args:
            symbol: Trading symbol to close position for

        Returns:
            Dict containing closure details

        Raises:
            Exception: If position closure fails
        """
        try:
            r = positions.PositionClose(
                accountID=self.account_id,
                instrument=symbol,
                data={"longUnits": "ALL"}  # Close all long positions
            )
            response = self.api.request(r)
            logger.info(f"Closed position for {symbol}")
            return response
        except Exception as e:
            logger.error(f"Error closing position: {str(e)}")
            raise


def create_paper_trader(broker: str, **credentials) -> PaperTrader:
    """Factory function to create a paper trader instance.

    Args:
        broker: 'alpaca' or 'oanda'
        **credentials: Broker-specific credentials
            For Alpaca: api_key, api_secret
            For Oanda: access_token, account_id

    Returns:
        PaperTrader instance

    Raises:
        ValueError: If broker is not supported
    """
    if broker.lower() == 'alpaca':
        return AlpacaPaperTrader(
            api_key=credentials['api_key'],
            api_secret=credentials['api_secret']
        )
    elif broker.lower() == 'oanda':
        return OandaPaperTrader(
            access_token=credentials['access_token'],
            account_id=credentials['account_id']
        )
    else:
        raise ValueError(f"Unsupported broker: {broker}")


if __name__ == "__main__":
    # Example usage
    alpaca_trader = create_paper_trader(
        'alpaca',
        api_key='YOUR_ALPACA_API_KEY',
        api_secret='YOUR_ALPACA_API_SECRET'
    )

    oanda_trader = create_paper_trader(
        'oanda',
        access_token='YOUR_OANDA_ACCESS_TOKEN',
        account_id='YOUR_OANDA_ACCOUNT_ID'
    )
