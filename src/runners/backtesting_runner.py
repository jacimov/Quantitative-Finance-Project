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

    Raises:
        ValueError: If required parameters are missing or invalid
    """
    # Validate data
    required_columns = ['Open', 'High', 'Low', 'Close', 'Volume']
    if not all(col in data.columns for col in required_columns):
        raise ValueError(
            f"Data must contain all required columns: {required_columns}"
        )

    # Validate parameters
    required_params = [
        'position_size',
        'atr_period',
        'high_period',
        'low_period',
        'lower_band_multiplier',
        'upper_band_multiplier',
        'long_size',
        'short_size'
    ]
    if not all(param in params for param in required_params):
        raise ValueError(
            f"Parameters must contain all required fields: {required_params}"
        )

    # Validate numeric parameters
    for param, value in params.items():
        if not isinstance(value, (int, float)):
            raise ValueError(
                f"Parameter {param} must be numeric, got {type(value)}"
            )

    # Create and run backtest
    bt = Backtest(
        data,
        OptimizedLongShortStrategy,
        cash=cash,
        commission=commission
    )
    return bt.run(**params)
