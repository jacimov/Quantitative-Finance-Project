"""
Hydra-Based Walk-Forward Optimization Main Script

This script implements a Hydra-based version of the walk-forward optimization
for forex trading strategies. It extends the base walk-forward optimization
with enhanced parameter search capabilities and is designed for deployment
in a high-performance computing environment.

Key Features:
- Hydra configuration management
- Extended parameter search space
- Larger currency pair coverage (40 pairs)
- Finer parameter granularity
- High-performance computing optimization

The script follows a systematic approach:
1. Load and prepare forex data
2. Perform walk-forward optimization with fine-grained parameters
3. Generate detailed performance visualizations
4. Calculate comprehensive performance metrics
5. Store results in a structured format
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
    Main execution function for the Hydra-based walk-forward optimization.

    This function implements an enhanced version
    of the walk-forward optimization
    process with finer parameter granularity
    and broader currency pair coverage.
    It is designed for deployment in high-performance computing environments.

    The function orchestrates:
    1. Environment setup and configuration
    2. Extended parameter space definition
    3. Multi-currency pair analysis
    4. Comprehensive performance evaluation
    5. Detailed results storage

    Constants:
        DATA_FOLDER: Location of forex data files
        INITIAL_CAPITAL: Starting capital for backtesting
        COMMISSION: Trading commission rate
        RISK_FREE_RATE: Risk-free rate for performance calculations

    Features:
        - Finer parameter granularity
        - Extended currency pair coverage (40 pairs)
        - Enhanced performance metrics
        - Structured results storage
        - Detailed visualization generation
    """
    # Set the working directory explicitly
    os.chdir("/home/njacimov/Quantitative-Finance-Project")
    print(f"Current working directory: {os.getcwd()}")

    # Constants
    DATA_FOLDER = "/home/njacimov/Algo_Trading/data/2y_1h_OHLC_FOREX"
    INITIAL_CAPITAL = 100000
    COMMISSION = 0.02
    RISK_FREE_RATE = 0.0456

    # Create a timestamp for the results folder
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    results_folder = f"results_{timestamp}"
    results_folder_path = os.path.abspath(results_folder)
    os.makedirs(results_folder_path, exist_ok=True)
    print(f"Results folder path: {results_folder_path}")

    # Define fine-grained parameter ranges
    param_ranges = {
        'position_size': np.arange(0.1, 1.0, 0.1),
        'atr_period': range(3, 15, 3),
        'high_period': range(3, 15, 3),
        'lower_band_multiplier': np.arange(1.5, 3.0, 0.25),
        'upper_band_multiplier': np.arange(1.5, 3.0, 0.25),
        'long_size': np.arange(0.2, 1.0, 0.1),
        'short_size': np.arange(0.2, 1.0, 0.1)
    }

    optimization_targets = ['sharpe', 'return']

    # Process extended set of currency pairs
    currency_pairs = get_currency_pairs(DATA_FOLDER, limit=40)

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
                    f"Start: {result['start_date']}, End: {result['end_date']}"
                )
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
            cumsum_returns = (1 + test_data['Close'].pct_change()).cumsum()
            buy_hold_equity = INITIAL_CAPITAL * cumsum_returns

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

    # Calculate and save summary statistics
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
