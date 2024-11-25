import os
from datetime import datetime
import numpy as np
import pandas as pd

from data_processing import load_forex_data, get_currency_pairs
from train_test_split import split_data
from optimization import optimize_strategy
from backtesting_runner import run_single_backtest
from utils import (
    calculate_annualized_return,
    calculate_max_drawdown,
    calculate_sharpe_ratio
)
from visualization import plot_heatmaps, plot_equity_curves


def main():
    # Constants
    DATA_FOLDER = (
        "/Users/niccolo/Desktop/Quant Finance/Code/Returns_and_Backtest/"
        "FOREX/Algo_Trading/data/2y_1h_OHLC_FOREX"
    )
    INITIAL_CAPITAL = 100000
    COMMISSION = 0.0001
    RISK_FREE_RATE = 0.02

    # Create a timestamp for the results folder
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    results_folder = f"results_{timestamp}"
    os.makedirs(results_folder, exist_ok=True)

    # Parameter ranges
    param_ranges = {
        'position_size': np.arange(0.1, 1.0, 0.25),
        'atr_period': range(3, 15, 5),
        'high_period': range(3, 15, 5),
        'lower_band_multiplier': np.arange(1.5, 3.0, 0.5),
        'upper_band_multiplier': np.arange(1.5, 3.0, 0.5),
        'long_size': np.arange(0.2, 1.0, 0.2),
        'short_size': np.arange(0.2, 1.0, 0.2)
    }

    optimization_targets = ['sharpe', 'return']

    # Get the first 10 currency pairs from the data folder
    currency_pairs = get_currency_pairs(DATA_FOLDER, limit=10)

    all_results = {target: [] for target in optimization_targets}
    top_performers = []

    for CURRENCY_PAIR in currency_pairs:
        print(f"\nProcessing {CURRENCY_PAIR}")

        # Load ForEx hourly data
        data = load_forex_data(DATA_FOLDER, CURRENCY_PAIR)

        # Split the data into train (2/3) and test (1/3) sets
        train_data, test_data = split_data(data)

        currency_folder = os.path.join(results_folder, CURRENCY_PAIR)
        os.makedirs(currency_folder, exist_ok=True)

        for target in optimization_targets:
            print(f"\nOptimizing for {target}")
            best_params, best_train_metric, best_test_metric, optimization_results = (
                optimize_strategy(train_data, test_data, param_ranges, target)
            )

            print(f"Best parameters: {best_params}")
            print(f"Best train metric: {best_train_metric}")
            print(f"Best test metric: {best_test_metric}")

            # Run backtest on test data with best parameters
            bt_results = run_single_backtest(
                test_data,
                best_params,
                cash=INITIAL_CAPITAL,
                commission=COMMISSION
            )

            print(f"Backtest results: {bt_results}")

            equity_curve = bt_results['_equity_curve']['Equity'].values
            annualized_return = calculate_annualized_return(equity_curve)
            max_drawdown = calculate_max_drawdown(equity_curve)
            sharpe_ratio = calculate_sharpe_ratio(equity_curve, RISK_FREE_RATE)

            result = {
                'currency_pair': CURRENCY_PAIR,
                'optimization_target': target,
                **best_params,
                'train_metric': best_train_metric,
                'test_metric': best_test_metric,
                'annualized_return': annualized_return,
                'max_drawdown': max_drawdown,
                'sharpe_ratio': sharpe_ratio,
                'end_equity': equity_curve[-1]
            }

            all_results[target].append(result)

            # Plot heatmaps
            plot_heatmaps(
                optimization_results,
                param_ranges,
                target,
                currency_folder
            )

            # Calculate buy and hold equity curve
            buy_hold_equity = (
                INITIAL_CAPITAL * (1 + test_data['Close'].pct_change())
            ).cumsum()

            # Plot equity curves comparison
            plot_equity_curves(
                equity_curve,
                buy_hold_equity,
                test_data,
                CURRENCY_PAIR,
                currency_folder
            )

        # Add to top performers list
        top_performers.append({
            'currency_pair': CURRENCY_PAIR,
            'end_equity': equity_curve[-1]
        })

        # Save results for this currency pair
        for target in optimization_targets:
            target_folder = os.path.join(
                currency_folder,
                f"{target}_optimization"
            )
            os.makedirs(target_folder, exist_ok=True)

            df = pd.DataFrame(all_results[target])
            df.to_csv(
                os.path.join(
                    target_folder,
                    f"optimization_results_{target}.csv"
                ),
                index=False
            )

    # Calculate and print summary statistics
    summary_stats = {}
    for target in optimization_targets:
        df = pd.DataFrame(all_results[target])

        numeric_columns = df.select_dtypes(include=[np.number]).columns
        non_numeric_columns = df.select_dtypes(exclude=[np.number]).columns

        mean_params = df[numeric_columns].mean()
        std_params = df[numeric_columns].std()

        # Ensure 'annualized_return' is in mean_params and std_params
        if ('annualized_return' in mean_params and
                'annualized_return' in std_params):
            lowest_feasible_return = (
                mean_params['annualized_return'] -
                3 * std_params['annualized_return']
            )
        else:
            lowest_feasible_return = None
            print(
                f"Warning: 'annualized_return' not found in results for {target}"
            )

        summary_stats[target] = {
            'optimization_target': target,
            **{f'mean_{col}': val for col, val in mean_params.items()},
            **{f'std_{col}': val for col, val in std_params.items()},
            'lowest_feasible_return': lowest_feasible_return
        }

        for col in non_numeric_columns:
            summary_stats[target][col] = df[col].iloc[0]

        print(f"\nSummary statistics for {target} optimization:")
        for key, value in summary_stats[target].items():
            print(f"{key}: {value}")

    # Save summary statistics
    summary_df = pd.DataFrame(summary_stats.values())
    summary_df.to_csv(
        os.path.join(results_folder, 'summary_statistics.csv'),
        index=False
    )

    # Sort and print top 5 performers
    top_performers.sort(key=lambda x: x['end_equity'], reverse=True)
    print("\nTop 5 Performers (Optimized End Equity):")
    for i, performer in enumerate(top_performers[:5], 1):
        print(
            f"{i}. {performer['currency_pair']}: ${performer['end_equity']:,.2f}"
        )

    # Save top 5 performers to CSV
    top_performers_df = pd.DataFrame(top_performers[:5])
    top_performers_df.to_csv(
        os.path.join(results_folder, 'top_5_performers.csv'),
        index=False
    )

    print(
        f"\nAll results, summary statistics, and top performers have been saved "
        f"in the '{results_folder}' directory."
    )


if __name__ == "__main__":
    main()
