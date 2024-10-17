# utils.py
import numpy as np
import pandas as pd

def calculate_annualized_return(equity_curve):
    if isinstance(equity_curve, np.ndarray):
        equity_curve = pd.Series(equity_curve)
    total_return = equity_curve.iloc[-1] / equity_curve.iloc[0] - 1
    years = len(equity_curve) / 252  # Assuming 252 trading days per year
    return (1 + total_return) ** (1 / years) - 1

def calculate_max_drawdown(equity_curve):
    if isinstance(equity_curve, np.ndarray):
        equity_curve = pd.Series(equity_curve)
    peak = equity_curve.cummax()
    drawdown = (equity_curve - peak) / peak
    return drawdown.min()

def calculate_sharpe_ratio(equity_curve, risk_free_rate):
    if isinstance(equity_curve, np.ndarray):
        equity_curve = pd.Series(equity_curve)
    returns = equity_curve.pct_change().dropna()
    excess_returns = returns - risk_free_rate / 252  # Assuming 252 trading days per year
    return np.sqrt(252) * excess_returns.mean() / excess_returns.std()

def calculate_sortino_ratio(equity_curve, risk_free_rate, target_return=0):
    if isinstance(equity_curve, np.ndarray):
        equity_curve = pd.Series(equity_curve)
    returns = equity_curve.pct_change().dropna()
    downside_returns = returns[returns < target_return]
    
    excess_return = returns.mean() - (risk_free_rate / 252)  # Assuming 252 trading days per year
    
    if len(downside_returns) == 0:
        # If there are no negative returns, return a high value (e.g., 100) or np.inf
        return 100  # or np.inf
    
    downside_std = downside_returns.std()
    
    if downside_std == 0:
        # If downside_std is zero, return 0 to avoid divide by zero
        return 0
    
    sortino_ratio = np.sqrt(252) * excess_return / downside_std
    return sortino_ratio
