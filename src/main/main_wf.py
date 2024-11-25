"""
Walk-Forward Optimization Main Script

This script implements the main execution flow for walk-forward optimization
of forex trading strategies. It provides comprehensive functionality for:
1. Data loading and preprocessing
2. Parameter optimization
3. Strategy backtesting
4. Performance visualization
5. Results analysis and storage

Key Features:
- Multiple currency pair analysis
- Multiple optimization targets (Sharpe ratio, returns)
- Parallel processing for efficiency
- Comprehensive performance metrics
- Automated result visualization and storage

The script follows a systematic approach:
1. Load and prepare forex data
2. Perform walk-forward optimization
3. Generate performance visualizations
4. Calculate and store performance metrics
5. Compare against buy-and-hold benchmark
"""

import os
from collections import Counter
from datetime import datetime
from itertools import product
import numpy as np
import pandas as pd
from tqdm import tqdm

from backtesting_runner import run_single_backtest
from data_processing import get_currency_pairs, load_forex_data
from optimization import run_backtest_with_params
from train_test_split import split_data
from utils import (
    calculate_annualized_return,
    calculate_max_drawdown,
    calculate_sharpe_ratio,
    calculate_sortino_ratio
)
from visualization import plot_equity_curves, plot_heatmaps
from walk_forward_optimization import (
    aggregate_walk_forward_results,
    walk_forward_optimization
)


def main():
    """
    Main execution function for the walk-forward optimization process.

    This function orchestrates the entire optimization workflow:
    1. Sets up the environment and constants
    2. Loads and processes forex data
    3. Performs walk-forward optimization
    4. Generates visualizations
    5. Calculates performance metrics
    6. Stores results

    The function handles multiple currency pairs and optimization targets,
    generating comprehensive performance analysis for each combination.

    Constants:
        DATA_FOLDER: Location of forex data files
        INITIAL_CAPITAL: Starting capital for backtesting
        COMMISSION: Trading commission rate
        RISK_FREE_RATE: Risk-free rate for Sharpe ratio calculation

    Results:
        - Creates a timestamped results folder
        - Generates CSV files with optimization results
        - Produces visualization plots
        - Calculates summary statistics
    """
    # Set the working directory explicitly
    os.chdir("/Users/niccolo/Desktop/Quant Finance/Code/BlackBoxes")
    print(f"Current working directory: {os.getcwd()}")

    # Constants
    DATA_FOLDER = (
        "/Users/niccolo/Desktop/Quant Finance/Code/Returns_and_Backtest/"
        "FOREX/Algo_Trading/data/2y_1h_OHLC_FOREX"
    )
    INITIAL_CAPITAL = 100000
    COMMISSION = 0.02
    RISK_FREE_RATE = 0.0456

    # Create a timestamp for the results folder
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    results_folder = f"results_{timestamp}"
    results_folder_path = os.path.abspath(results_folder)
    os.makedirs(results_folder_path, exist_ok=True)
    print(f"Results folder path: {results_folder_path}")

    # Define parameter ranges for optimization
    param_ranges = {
        'position_size': np.arange(0.1, 1.0, 0.5),
        'atr_period': range(3, 15, 8),
        'high_period': range(3, 15, 8),
        'lower_band_multiplier': np.arange(1.5, 3.0, 1.25),
        'upper_band_multiplier': np.arange(1.5, 3.0, 1.25),
        'long_size': np.arange(0.2, 1.0, 0.2),
        'short_size': np.arange(0.2, 1.0, 0.2)
    }

    optimization_targets = ['sharpe', 'return']

    # Get the first 10 currency pairs from the data folder
    currency_pairs = get_currency_pairs(DATA_FOLDER, limit=10)

    all_results = {target: [] for target in optimization_targets}
    top_performers = []

    # Process each currency pair
    for CURRENCY_PAIR in currency_pairs:
        print(f"\nProcessing {CURRENCY_PAIR}")

        # Load and split forex data
        data = load_forex_data(DATA_FOLDER, CURRENCY_PAIR)
        train_data, test_data = split_data(data, train_ratio=0.75)

        # Create currency-specific results folder
        currency_folder = os.path.join(
            results_folder_path,
            os.path.basename(CURRENCY_PAIR)
        )
        os.makedirs(currency_folder, exist_ok=True)
        print(f"Currency folder path: {currency_folder}")

        # Process each optimization target
        for target in optimization_targets:
            print(f"\nOptimizing for {target}")

            # Perform walk-forward optimization
            wfo_results, best_params_list = walk_forward_optimization(
                train_data,
                param_ranges,
                target,
                train_ratio=0.6,
                test_ratio=0.2
            )

            # Debug output
            print("Debug: First few WFO results:")
            for result in wfo_results[:3]:
                print(
                    f"Start: {result['start_date']}, End: {result['end_date']}")
                print(f"Best params: {result['best_params']}")
                print(
                    f"Train metric: {result['train_metric']}, "
                    f"Test metric: {result['test_metric']}"
                )
                print("---")

            # Generate visualizations
            plot_heatmaps(wfo_results, param_ranges, target, currency_folder)

            # Aggregate optimization results
            best_params, avg_train_metric, avg_test_metric = (
                aggregate_walk_forward_results(wfo_results)
            )

            print(f"Debug: Aggregated best parameters: {best_params}")
            print(f"Debug: Average train metric: {avg_train_metric}")
            print(f"Debug: Average test metric: {avg_test_metric}")

            # Flatten nested parameters if necessary
            if ('position_size' in best_params and
                    isinstance(best_params['position_size'], dict)):
                best_params = {
                    **best_params,
                    **best_params.pop('position_size')
                }

            print(f"Debug: Final best parameters for backtest: {best_params}")

            # Run final backtest with best parameters
            bt_results = run_single_backtest(
                test_data,
                best_params,
                cash=INITIAL_CAPITAL,
                commission=COMMISSION
            )

            print(f"Backtest results: {bt_results}")

            # Calculate performance metrics
            equity_curve = bt_results['_equity_curve']['Equity'].values
            annualized_return = calculate_annualized_return(equity_curve)
            max_drawdown = calculate_max_drawdown(equity_curve)
            sharpe_ratio = calculate_sharpe_ratio(equity_curve, RISK_FREE_RATE)
            sortino_ratio = calculate_sortino_ratio(
                equity_curve,
                RISK_FREE_RATE
            )

            # Store results
            result = {
                'currency_pair': CURRENCY_PAIR,
                'optimization_target': target,
                **best_params,
                'avg_train_metric': avg_train_metric,
                'avg_test_metric': avg_test_metric,
                'final_test_annualized_return': annualized_return,
                'final_test_max_drawdown': max_drawdown,
                'final_test_sharpe_ratio': sharpe_ratio,
                'final_test_sortino_ratio': sortino_ratio,
                'final_test_end_equity': equity_curve[-1]
            }

            all_results[target].append(result)

            # Calculate and plot benchmark comparison
            buy_hold_equity = (INITIAL_CAPITAL *
                               (1 + test_data['Close'].pct_change().cumsum()))

            plot_equity_curves(
                equity_curve,
                buy_hold_equity,
                test_data,
                CURRENCY_PAIR,
                currency_folder
            )

            # Save results
            target_folder = os.path.join(
                currency_folder,
                f"{target}_optimization"
            )
            os.makedirs(target_folder, exist_ok=True)

            result_df = pd.DataFrame([result])
            result_df.to_csv(
                os.path.join(
                    target_folder,
                    f'optimization_results_{target}.csv'
                ),
                index=False
            )

        # Track top performing strategies
        top_performers.append({
            'currency_pair': CURRENCY_PAIR,
            'end_equity': equity_curve[-1]
        })

    # Calculate summary statistics
    summary_stats = {}
    for target in optimization_targets:
        results_df = pd.DataFrame(all_results[target])
        
        summary_stats[target] = {
            'mean_return': results_df['final_test_annualized_return'].mean(),
            'mean_sharpe': results_df['final_test_sharpe_ratio'].mean(),
            'mean_sortino': results_df['final_test_sortino_ratio'].mean(),
            'mean_drawdown': results_df['final_test_max_drawdown'].mean()
        }

        # Save summary statistics
        summary_df = pd.DataFrame([summary_stats[target]])
        summary_df.to_csv(
            os.path.join(
                results_folder_path,
                f'summary_stats_{target}.csv'
            ),
            index=False
        )

    # Save top performers
    top_performers_df = pd.DataFrame(top_performers)
    top_performers_df.to_csv(
        os.path.join(results_folder_path, 'top_performers.csv'),
        index=False
    )


if __name__ == "__main__":
    main()
