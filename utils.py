"""
Trading Strategy Performance Metrics Module

This module provides utility functions for calculating various performance
metrics commonly used in quantitative trading strategies:
- Annualized Return
- Maximum Drawdown
- Sharpe Ratio
- Sortino Ratio

All functions accept both numpy arrays and pandas Series as input for
the equity curve calculations.
"""

import numpy as np
import pandas as pd


def calculate_annualized_return(equity_curve):
    """
    Calculate the annualized return from an equity curve.

    This function converts the total return over the trading period into
    an annualized rate, assuming 252 trading days per year.

    Args:
        equity_curve (Union[np.ndarray, pd.Series]): Array or Series of
            portfolio values over time

    Returns:
        float: Annualized return as a decimal (e.g., 0.15 for 15% return)
    """
    if isinstance(equity_curve, np.ndarray):
        equity_curve = pd.Series(equity_curve)
    total_return = (
        equity_curve.iloc[-1] / equity_curve.iloc[0] - 1
    )
    # Assuming 252 trading days per year
    years = len(equity_curve) / 252
    return (1 + total_return) ** (1 / years) - 1


def calculate_max_drawdown(equity_curve):
    """
    Calculate the maximum drawdown from peak for an equity curve.

    Maximum drawdown measures the largest peak-to-trough decline in the
    portfolio value, expressed as a percentage of the peak value.

    Args:
        equity_curve (Union[np.ndarray, pd.Series]): Array or Series of
            portfolio values over time

    Returns:
        float: Maximum drawdown as a decimal (e.g., -0.20 for 20% drawdown)
    """
    if isinstance(equity_curve, np.ndarray):
        equity_curve = pd.Series(equity_curve)
    peak = equity_curve.cummax()
    drawdown = (equity_curve - peak) / peak
    return drawdown.min()


def calculate_sharpe_ratio(equity_curve, risk_free_rate):
    """
    Calculate the Sharpe ratio for an equity curve.

    The Sharpe ratio measures the risk-adjusted return of the portfolio,
    comparing excess returns (over risk-free rate) to volatility.

    Args:
        equity_curve (Union[np.ndarray, pd.Series]): Array or Series of
            portfolio values over time
        risk_free_rate (float): Annual risk-free rate as decimal
            (e.g., 0.02 for 2%)

    Returns:
        float: Sharpe ratio
        (higher values indicate better risk-adjusted returns)
    """
    if isinstance(equity_curve, np.ndarray):
        equity_curve = pd.Series(equity_curve)
    returns = equity_curve.pct_change().dropna()
    # Assuming 252 trading days per year
    excess_returns = returns - (risk_free_rate / 252)
    return (
        np.sqrt(252) * excess_returns.mean() / excess_returns.std()
    )


def calculate_sortino_ratio(equity_curve, risk_free_rate, target_return=0):
    """
    Calculate the Sortino ratio for an equity curve.

    The Sortino ratio is similar to the Sharpe ratio but only penalizes
    returns below a target rate, typically zero. It measures the
    risk-adjusted return considering only downside volatility.

    Args:
        equity_curve (Union[np.ndarray, pd.Series]): Array or Series of
            portfolio values over time
        risk_free_rate (float): Annual risk-free rate as decimal
            (e.g., 0.02 for 2%)
        target_return (float, optional): Minimum acceptable return,
            defaults to 0

    Returns:
        float: Sortino ratio (higher values indicate better
            risk-adjusted returns with less downside risk)
    """
    if isinstance(equity_curve, np.ndarray):
        equity_curve = pd.Series(equity_curve)
    returns = equity_curve.pct_change().dropna()
    downside_returns = returns[returns < target_return]

    # Assuming 252 trading days per year
    excess_return = returns.mean() - (risk_free_rate / 252)

    if len(downside_returns) == 0:
        # If there are no negative returns, return a high value (e.g., 100)
        return 100  # or np.inf

    downside_std = downside_returns.std()

    if downside_std == 0:
        # If downside_std is zero, return 0 to avoid divide by zero
        return 0

    sortino_ratio = (
        np.sqrt(252) * excess_return / downside_std
    )
    return sortino_ratio
