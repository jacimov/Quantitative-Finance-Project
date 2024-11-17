"""
Backtesting Runner Module

This module provides a streamlined interface for running backtests using the
OptimizedLongShortStrategy. It encapsulates the backtesting configuration
and execution process, making it easy to:
- Run individual backtests with custom parameters
- Configure initial capital and commission rates
- Generate comprehensive performance metrics

The module uses the backtesting.py library for strategy execution and
performance analysis.
"""

from backtesting import Backtest
from trading_strategy import OptimizedLongShortStrategy


def run_single_backtest(
    data, params, cash=100000, commission=0.0001
):
    """
    Run a single backtest with specified parameters and data.

    This function creates and executes a backtest using the
    OptimizedLongShortStrategy with custom parameters. It provides a simple
    interface for testing trading strategies with different configurations.

    Args:
        data (pd.DataFrame): OHLCV data for backtesting
        params (dict): Strategy parameters including:
            - position_size: Base position size (0-1)
            - atr_period: Period for ATR calculation
            - high_period: Period for trailing high calculation
            - low_period: Period for trailing low calculation
            - lower_band_multiplier: Multiplier for lower band
            - upper_band_multiplier: Multiplier for upper band
            - long_size: Size multiplier for long positions
            - short_size: Size multiplier for short positions
        cash (float, optional): Initial capital. Defaults to 100,000
        commission (float, optional): Commission rate per trade.
            Defaults to 0.0001 (0.01%)

    Returns:
        backtesting.backtesting.Result: Backtest results containing:
            - Performance metrics (returns, Sharpe ratio, etc.)
            - Trade history
            - Equity curve
            - Position sizes and values
    """
    bt = Backtest(
        data,
        OptimizedLongShortStrategy,
        cash=cash,
        commission=commission
    )
    return bt.run(**params)
