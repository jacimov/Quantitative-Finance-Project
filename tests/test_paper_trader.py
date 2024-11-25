"""Unit tests for paper_trader.py."""

import unittest
from unittest.mock import MagicMock, patch
import json

from paper_trader import (
    AlpacaPaperTrader,
    create_paper_trader
)


class TestAlpacaPaperTrader(unittest.TestCase):
    """Test cases for AlpacaPaperTrader class."""

    def setUp(self):
        """Set up test fixtures."""
        self.api_key = "test_key"
        self.api_secret = "test_secret"
        with patch('alpaca_trade_api.REST') as mock_rest:
            self.mock_api = mock_rest.return_value
            self.trader = AlpacaPaperTrader(self.api_key, self.api_secret)

    def test_place_market_order(self):
        """Test placing a market order."""
        # Setup
        mock_order = MagicMock()
        mock_order._raw = {"id": "test_order", "status": "filled"}
        self.mock_api.submit_order.return_value = mock_order

        # Execute
        result = self.trader.place_order("AAPL", 1, "buy")

        # Verify
        self.mock_api.submit_order.assert_called_once_with(
            symbol="AAPL",
            qty=1,
            side="buy",
            type="market",
            limit_price=None,
            time_in_force="gtc"
        )
        self.assertEqual(result, {"id": "test_order", "status": "filled"})

    def test_place_limit_order(self):
        """Test placing a limit order."""
        # Setup
        mock_order = MagicMock()
        mock_order._raw = {"id": "test_order", "status": "new"}
        self.mock_api.submit_order.return_value = mock_order

        # Execute
        result = self.trader.place_order(
            "AAPL", 1, "buy", order_type="limit", limit_price=150.0
        )

        # Verify
        self.mock_api.submit_order.assert_called_once_with(
            symbol="AAPL",
            qty=1,
            side="buy",
            type="limit",
            limit_price=150.0,
            time_in_force="gtc"
        )
        self.assertEqual(result, {"id": "test_order", "status": "new"})

    def test_get_positions(self):
        """Test getting positions."""
        # Setup
        mock_position = MagicMock()
        mock_position._raw = {"symbol": "AAPL", "qty": 1}
        self.mock_api.list_positions.return_value = [mock_position]

        # Execute
        result = self.trader.get_positions()

        # Verify
        self.mock_api.list_positions.assert_called_once()
        self.assertEqual(result, [{"symbol": "AAPL", "qty": 1}])

    def test_close_position(self):
        """Test closing a position."""
        # Setup
        mock_response = MagicMock()
        mock_response._raw = {"symbol": "AAPL", "status": "closed"}
        self.mock_api.close_position.return_value = mock_response

        # Execute
        result = self.trader.close_position("AAPL")

        # Verify
        self.mock_api.close_position.assert_called_once_with("AAPL")
        self.assertEqual(result, {"symbol": "AAPL", "status": "closed"})


class TestCreatePaperTrader(unittest.TestCase):
    """Test cases for create_paper_trader function."""

    def test_create_alpaca_trader(self):
        """Test creating an Alpaca paper trader."""
        trader = create_paper_trader(
            'alpaca',
            api_key='test_key',
            api_secret='test_secret'
        )
        self.assertIsInstance(trader, AlpacaPaperTrader)

    def test_create_invalid_broker(self):
        """Test creating a paper trader with invalid broker."""
        with self.assertRaises(ValueError):
            create_paper_trader('invalid_broker')


if __name__ == '__main__':
    unittest.main()
