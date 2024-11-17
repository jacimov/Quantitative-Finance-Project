"""
Live Trading Module

This module implements live trading functionality using the OptimizedLongShortStrategy.
It handles:
1. Real-time market data streaming
2. Signal generation using the strategy
3. Trade execution and position management
4. Risk monitoring and reporting
"""

import ccxt
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import time
import logging
from trading_strategy import OptimizedLongShortStrategy

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class LiveTrader:
    """
    Live Trading Implementation.

    This class manages the live trading process, including:
    - Market data collection
    - Signal generation
    - Trade execution
    - Position management
    """

    def __init__(
        self,
        exchange_id='binance',
        symbol='BTC/USDT',
        timeframe='5m',
        api_key=None,
        api_secret=None,
        strategy_params=None
    ):
        """
        Initialize the live trader.

        Args:
            exchange_id (str): The exchange to trade on (e.g., 'binance')
            symbol (str): Trading pair symbol (e.g., 'BTC/USDT')
            timeframe (str): Candle timeframe (e.g., '5m', '15m', '1h')
            api_key (str): Exchange API key
            api_secret (str): Exchange API secret
            strategy_params (dict): Parameters for the trading strategy
        """
        self.exchange_id = exchange_id
        self.symbol = symbol
        self.timeframe = timeframe

        # Initialize exchange connection
        exchange_class = getattr(ccxt, exchange_id)
        self.exchange = exchange_class({
            'apiKey': api_key,
            'secret': api_secret,
            'enableRateLimit': True
        })

        # Initialize strategy parameters
        self.strategy_params = strategy_params or {
            'position_size': 0.95,
            'atr_period': 5,
            'high_period': 5,
            'low_period': 5,
            'lower_band_multiplier': 2.25,
            'upper_band_multiplier': 2.25,
            'long_size': 1.0,
            'short_size': 1.0
        }

        # Initialize strategy instance
        self.strategy = OptimizedLongShortStrategy

        # Track positions and orders
        self.current_position = 0
        self.active_orders = {}

    def fetch_ohlcv_data(self, limit=100):
        """
        Fetch recent OHLCV data from the exchange.

        Args:
            limit (int): Number of candles to fetch

        Returns:
            pd.DataFrame: OHLCV data
        """
        try:
            ohlcv = self.exchange.fetch_ohlcv(
                self.symbol,
                timeframe=self.timeframe,
                limit=limit
            )

            df = pd.DataFrame(
                ohlcv,
                columns=['timestamp', 'Open', 'High', 'Low', 'Close', 'Volume']
            )
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            df.set_index('timestamp', inplace=True)
            return df

        except Exception as e:
            logger.error(f"Error fetching OHLCV data: {e}")
            return None

    def calculate_signals(self, data):
        """
        Calculate trading signals using the strategy.

        Args:
            data (pd.DataFrame): OHLCV data

        Returns:
            dict: Trading signals including entry/exit points and position sizes
        """
        # Initialize strategy with current data
        strategy = self.strategy(**self.strategy_params)
        strategy.data = data
        strategy.init()

        # Get latest indicator values
        current_price = data['Close'].iloc[-1]
        lower_band = strategy.calculate_lower_band(data)[-1]
        upper_band = strategy.calculate_upper_band(data)[-1]
        trailing_high = strategy.calculate_high(strategy.high_period)[-1]
        trailing_low = strategy.calculate_low(strategy.low_period)[-1]

        # Generate signals
        signals = {
            'price': current_price,
            'lower_band': lower_band,
            'upper_band': upper_band,
            'trailing_high': trailing_high,
            'trailing_low': trailing_low,
            'long_entry': current_price < lower_band,
            'short_entry': current_price > upper_band,
            'long_exit': current_price > trailing_high,
            'short_exit': current_price < trailing_low
        }

        return signals

    def execute_trade(self, side, amount):
        """
        Execute a trade on the exchange.

        Args:
            side (str): 'buy' or 'sell'
            amount (float): Amount to trade

        Returns:
            dict: Order information
        """
        try:
            order = self.exchange.create_order(
                symbol=self.symbol,
                type='market',
                side=side,
                amount=amount
            )
            logger.info(f"Executed {side} order: {amount} {self.symbol}")
            return order

        except Exception as e:
            logger.error(f"Error executing trade: {e}")
            return None

    def manage_positions(self, signals):
        """
        Manage trading positions based on signals.

        Args:
            signals (dict): Trading signals
        """
        try:
            # Get account balance
            balance = self.exchange.fetch_balance()
            available_balance = balance['total']['USDT']

            # Calculate position sizes
            position_value = available_balance * \
                self.strategy_params['position_size']

            # Check for exit signals first
            if self.current_position > 0 and signals['long_exit']:
                # Close long position
                self.execute_trade('sell', abs(self.current_position))
                self.current_position = 0
                logger.info("Closed long position")

            elif self.current_position < 0 and signals['short_exit']:
                # Close short position
                self.execute_trade('buy', abs(self.current_position))
                self.current_position = 0
                logger.info("Closed short position")

            # Check for entry signals
            if self.current_position == 0:
                if signals['long_entry']:
                    # Enter long position
                    amount = position_value / \
                        signals['price'] * self.strategy_params['long_size']
                    order = self.execute_trade('buy', amount)
                    if order:
                        self.current_position = amount

                elif signals['short_entry']:
                    # Enter short position
                    amount = position_value / \
                        signals['price'] * self.strategy_params['short_size']
                    order = self.execute_trade('sell', amount)
                    if order:
                        self.current_position = -amount

        except Exception as e:
            logger.error(f"Error managing positions: {e}")

    def run(self, interval_seconds=300):
        """
        Run the live trading loop.

        Args:
            interval_seconds (int): Seconds between each trading iteration
        """
        logger.info(
            f"Starting live trading for {self.symbol} on {self.exchange_id}")

        while True:
            try:
                # Fetch latest market data
                data = self.fetch_ohlcv_data()
                if data is None:
                    logger.warning("No data received, skipping iteration")
                    continue

                # Calculate signals
                signals = self.calculate_signals(data)

                # Manage positions based on signals
                self.manage_positions(signals)

                # Log current state
                logger.info(f"Current position: {self.current_position}")
                logger.info(f"Signals: {signals}")

                # Wait for next iteration
                time.sleep(interval_seconds)

            except Exception as e:
                logger.error(f"Error in trading loop: {e}")
                time.sleep(interval_seconds)


if __name__ == "__main__":
    # Example usage
    trader = LiveTrader(
        exchange_id='binance',
        symbol='BTC/USDT',
        timeframe='5m',
        api_key='YOUR_API_KEY',
        api_secret='YOUR_API_SECRET'
    )
    trader.run()
