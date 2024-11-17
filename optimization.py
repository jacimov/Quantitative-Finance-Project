"""
Strategy Optimization Module

This module implements parallel optimization for trading strategies using
multiprocessing. It provides functionality for:
1. Parameter optimization across multiple combinations
2. Parallel backtesting execution
3. Performance metric calculation and comparison

The module supports optimization for different targets:
- Sharpe ratio optimization
- Return optimization

Key features:
- Multiprocessing for faster execution
- Progress tracking with tqdm
- Flexible parameter space exploration
"""

import multiprocessing as mp
from itertools import product

import numpy as np
from tqdm import tqdm

from backtesting_runner import run_single_backtest
from utils import calculate_sharpe_ratio


def run_backtest_with_params(args):
    """
    Execute a single backtest w/ given params on both training and test data.

    This function runs a backtest with specified parameters and calculates
    performance metrics for both training and test datasets. It supports
    optimization for either Sharpe ratio or returns.

    Args:
        args (tuple): Contains:
            - params (dict): Strategy parameters
            - train_data (pd.DataFrame): Training dataset
            - test_data (pd.DataFrame): Test dataset
            - optimization_target (str): 'sharpe' or 'return'

    Returns:
        tuple: Contains:
            - params (dict): Input parameters
            - train_metric (float): Performance metric on training data
            - test_metric (float): Performance metric on test data
    """
    params, train_data, test_data, optimization_target = args
    bt_train_result = run_single_backtest(train_data, params)
    bt_test_result = run_single_backtest(test_data, params)

    # Extract equity curves
    train_equity_curve = bt_train_result['_equity_curve']['Equity'].values
    test_equity_curve = bt_test_result['_equity_curve']['Equity'].values

    # Calculate metrics based on optimization target
    if optimization_target == 'sharpe':
        train_metric = calculate_sharpe_ratio(train_equity_curve, 0.02)
        test_metric = calculate_sharpe_ratio(test_equity_curve, 0.02)
    elif optimization_target == 'return':
        train_metric = bt_train_result['Return [%]']
        test_metric = bt_test_result['Return [%]']

    return params, train_metric, test_metric


def optimize_strategy(train_data, test_data, param_ranges, optimization_target):
    """
    Optimize strategy parameters using parallel processing.

    This function performs a grid search over the parameter space to find the
    optimal combination of parameters that maximizes the chosen metric
    (Sharpe ratio or returns) on the training data, while also evaluating
    performance on test data to assess robustness.

    Args:
        train_data (pd.DataFrame): Training dataset
        test_data (pd.DataFrame): Test dataset
        param_ranges (dict): Dictionary of parameter names and their ranges
        optimization_target (str): Metric to optimize ('sharpe' or 'return')

    Returns:
        tuple: Contains:
            - best_params (dict): Best performing parameters
            - best_train_metric (float): Best metric value on training data
            - best_test_metric (float): Corresponding metric on test data
            - results (list): All optimization results

    Note:
        Uses multiprocessing to parallelize backtesting across CPU cores
    """
    best_train_metric = -np.inf
    best_params = None
    results = []

    # Generate all possible parameter combinations
    param_combinations = list(product(*param_ranges.values()))
    total_iterations = len(param_combinations)

    # Set up multiprocessing pool
    with mp.Pool(processes=mp.cpu_count()) as pool:
        desc = f"Optimizing {optimization_target}"
        with tqdm(total=total_iterations, desc=desc) as pbar:
            # Prepare arguments for parallel processing
            param_args = [
                (
                    dict(zip(param_ranges.keys(), p)),
                    train_data,
                    test_data,
                    optimization_target
                )
                for p in param_combinations
            ]

            # Execute backtests in parallel
            for result in pool.imap_unordered(
                run_backtest_with_params, param_args
            ):
                params, train_metric, test_metric = result
                results.append({**params, optimization_target: train_metric})

                # Update best parameters if current result is better
                if train_metric > best_train_metric:
                    best_train_metric = train_metric
                    best_params = params

                pbar.update()

    # Get test metric for best parameters
    best_test_metric = [
        r[optimization_target]
        for r in results
        if all(r[k] == v for k, v in best_params.items())
    ][0]

    return best_params, best_train_metric, best_test_metric, results
