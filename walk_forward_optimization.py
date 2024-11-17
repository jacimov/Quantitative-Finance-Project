"""
Walk Forward Optimization Module

This module implements walk-forward optimization
techniques for trading strategies.
It provides functionality to test and validate
trading strategies across multiple
time periods, helping prevent overfitting and ensuring strategy robustness.

The module uses a sliding window approach where the strategy is:
1. Trained on a training window
2. Tested on an out-of-sample window
3. Moved forward by a specified step size

Key Functions:
    - walk_forward_optimization: Performs walk-forward analysis
    - aggregate_walk_forward_results: Aggregates results from multiple periods
"""

from collections import Counter
from itertools import product

import numpy as np
from tqdm import tqdm

from optimization import optimize_strategy


def walk_forward_optimization(
    data,
    param_ranges,
    optimization_target,
    train_ratio=0.6,
    test_ratio=0.2
):
    """
    Perform walk-forward optimization on the trading strategy.

    This function implements a walk-forward analysis by:
    1. Dividing the data into training and testing windows
    2. Optimizing strategy parameters on the training window
    3. Testing the optimized parameters on the test window
    4. Moving the windows forward and repeating

    Args:
        data (pd.DataFrame): Historical price data for optimization
        param_ranges (dict): Dictionary of parameter ranges to test
        optimization_target (str): Metric to optimize ('sharpe' or 'return')
        train_ratio (float): Proportion of data to use for training
        test_ratio (float): Proportion of data to use for testing

    Returns:
        tuple: List of results for each period and list of best parameters
    """
    total_length = len(data)
    train_window = int(total_length * train_ratio)
    test_window = int(total_length * test_ratio)
    # We'll move forward by the size of the test window each time
    step_size = test_window

    results = []
    best_params_list = []

    steps = range(0, total_length - train_window - test_window + 1, step_size)
    for i in tqdm(steps):
        train_data = data.iloc[i:i + train_window]
        test_data = data.iloc[i + train_window:i + train_window + test_window]

        best_params, best_train_metric, best_test_metric, _ = (
            optimize_strategy(
                train_data,
                test_data,
                param_ranges,
                optimization_target
            )
        )

        print(f"Debug: Best params: {best_params}")
        print(f"Debug: Best train metric: {best_train_metric}")
        print(f"Debug: Best test metric: {best_test_metric}")

        results.append({
            'start_date': train_data.index[0],
            'end_date': test_data.index[-1],
            'best_params': best_params,
            'train_metric': best_train_metric,
            'test_metric': best_test_metric
        })

        best_params_list.append(best_params)

    return results, best_params_list


def aggregate_walk_forward_results(results):
    """
    Aggregate results from multiple walk-forward periods to determine optimal
    parameters.

    This function analyzes the performance across all walk-forward periods to:
    1. Identify consistently well-performing parameters
    2. Calculate average performance metrics
    3. Determine the most robust parameter set

    Args:
        results (list): List of dictionaries
        containing results from each period

    Returns:
        tuple: Best parameters, average train metric, and average test metric
    """
    all_params = [result['best_params'] for result in results]

    avg_params = {}
    for key in all_params[0].keys():
        values = [params[key] for params in all_params]
        if isinstance(values[0], dict):
            avg_params[key] = {}
            for subkey in values[0].keys():
                subvalues = [v[subkey] for v in values]
                if all(isinstance(v, (int, float)) for v in subvalues):
                    avg_params[key][subkey] = np.mean(subvalues)
                else:
                    avg_params[key][subkey] = max(
                        set(subvalues),
                        key=subvalues.count
                    )
        elif all(isinstance(v, (int, float)) for v in values):
            avg_params[key] = np.mean(values)
        else:
            avg_params[key] = max(set(values), key=values.count)

    # Convert integer parameters back to int
    int_params = ['atr_period', 'high_period', 'low_period']
    for key in int_params:
        if key in avg_params:
            avg_params[key] = int(round(avg_params[key]))
        elif isinstance(avg_params.get('position_size'), dict):
            if key in avg_params['position_size']:
                avg_params['position_size'][key] = int(
                    round(avg_params['position_size'][key])
                )

    avg_train_metric = np.mean([result['train_metric'] for result in results])
    avg_test_metric = np.mean([result['test_metric'] for result in results])

    return avg_params, avg_train_metric, avg_test_metric
