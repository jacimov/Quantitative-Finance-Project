"""
Optimized Long-Short Trading Strategy Module

This module implements an optimized long-short trading strategy using
technical indicators and price bands. The strategy:
1. Uses ATR (Average True Range) for volatility measurement
2. Implements dynamic price bands for entry signals
3. Uses trailing high/low values for exit signals
4. Supports position sizing optimization

Key Features:
- Dynamic volatility-based entry points
- Separate long and short position sizing
- Trailing stop-loss mechanism
- Customizable parameters for optimization
"""

import numpy as np
from backtesting import Strategy


class OptimizedLongShortStrategy(Strategy):
    """
    Optimized Long-Short Trading Strategy Implementation.

    This strategy uses a combination of technical indicators to generate
    trading signals:
    - ATR for volatility measurement
    - Price bands for entry signals
    - Trailing highs/lows for exit signals

    Parameters:
        position_size (float): Base position size (0-1)
        atr_period (int): Period for ATR calculation
        high_period (int): Period for trailing high calculation
        low_period (int): Period for trailing low calculation
        lower_band_multiplier (float): Multiplier for lower band calculation
        upper_band_multiplier (float): Multiplier for upper band calculation
        long_size (float): Size multiplier for long positions
        short_size (float): Size multiplier for short positions

    The strategy enters:
    - Long when price crosses below lower band
    - Short when price crosses above upper band

    Exits:
    - Long positions when price exceeds previous high
    - Short positions when price falls below previous low
    """
    position_size = 0.95
    atr_period = 5
    high_period = 5
    low_period = 5
    lower_band_multiplier = 2.25
    upper_band_multiplier = 2.25
    long_size = 1.0
    short_size = 1.0

    def init(self):
        """
        Initialize strategy indicators and parameters.

        This method:
        1. Converts period parameters to integers
        2. Initializes technical indicators:
           - ATR (Average True Range)
           - Trailing high values
           - Trailing low values
           - Upper and lower price bands
        """
        self.atr_period = int(self.atr_period)
        self.high_period = int(self.high_period)
        self.low_period = int(self.low_period)

        self.atr = self.I(self.calculate_atr, self.atr_period)
        self.high = self.I(self.calculate_high, self.high_period)
        self.low = self.I(self.calculate_low, self.low_period)
        self.lower_band = self.I(self.calculate_lower_band)
        self.upper_band = self.I(self.calculate_upper_band)

    def calculate_atr(self, period):
        """
        Calculate Average True Range (ATR).

        ATR measures market volatility by decomposing the entire range of an
        asset price for a specific period.

        Args:
            period (int): Number of periods for ATR calculation

        Returns:
            numpy.array: Array of ATR values
        """
        high = self.data.High
        low = self.data.Low
        close = self.data.Close
        tr = np.maximum(
            high - low,
            np.abs(high - np.roll(close, 1)),
            np.abs(low - np.roll(close, 1))
        )
        atr = np.zeros_like(tr)
        atr[:period] = np.nan
        for i in range(period, len(tr)):
            atr[i] = np.mean(tr[i - period + 1:i + 1])
        return atr

    def calculate_high(self, period):
        """
        Calculate trailing high values.

        Computes the highest price over a specified lookback period.

        Args:
            period (int): Lookback period for high calculation

        Returns:
            numpy.array: Array of trailing high values
        """
        high = self.data.High
        result = np.zeros_like(high)
        for i in range(len(high)):
            result[i] = np.max(high[max(0, i - period + 1):i + 1])
        return result

    def calculate_low(self, period):
        """
        Calculate trailing low values.

        Computes the lowest price over a specified lookback period.

        Args:
            period (int): Lookback period for low calculation

        Returns:
            numpy.array: Array of trailing low values
        """
        low = self.data.Low
        result = np.zeros_like(low)
        for i in range(len(low)):
            result[i] = np.min(low[max(0, i - period + 1):i + 1])
        return result

    def calculate_lower_band(self):
        """
        Calculate lower price band.

        The lower band is calculated as:
        high - (lower_band_multiplier * ATR)

        Returns:
            numpy.array: Array of lower band values
        """
        return self.high - self.lower_band_multiplier * self.atr

    def calculate_upper_band(self):
        """
        Calculate upper price band.

        The upper band is calculated as:
        low + (upper_band_multiplier * ATR)

        Returns:
            numpy.array: Array of upper band values
        """
        return self.low + self.upper_band_multiplier * self.atr

    def next(self):
        """
        Execute trading logic for the current candle.

        This method implements the core trading logic:
        1. Entry conditions:
           - Long: Price below lower band
           - Short: Price above upper band
        2. Position sizing:
           - Uses base position size modified by long/short multipliers
           - Caps position size at 0.99 (99% of available capital)
        3. Exit conditions:
           - Long: Price exceeds previous high
           - Short: Price falls below previous low
        """
        if not self.position:
            if self.data.Close[-1] < self.lower_band[-1]:
                size = min(self.position_size * self.long_size, 0.99)
                self.buy(size=size)
            elif self.data.Close[-1] > self.upper_band[-1]:
                size = min(self.position_size * self.short_size, 0.99)
                self.sell(size=size)
        elif self.position.is_long and self.data.Close[-1] > self.data.High[-2]:
            self.position.close()
        elif self.position.is_short and self.data.Close[-1] < self.data.Low[-2]:
            self.position.close()
