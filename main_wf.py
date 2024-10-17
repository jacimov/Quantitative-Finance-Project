# main_wf.py
import os
from datetime import datetime
import numpy as np
import pandas as pd
from itertools import product
from tqdm import tqdm
from collections import Counter

from data_processing import load_forex_data, get_currency_pairs
from train_test_split import split_data
from optimization import run_backtest_with_params
from backtesting_runner import run_single_backtest
from utils import calculate_annualized_return, calculate_max_drawdown, calculate_sharpe_ratio, calculate_sortino_ratio
from visualization import plot_equity_curves, plot_heatmaps
from walk_forward_optimization import walk_forward_optimization, aggregate_walk_forward_results

def main():
    # Set the working directory explicitly
    os.chdir("/Users/niccolo/Desktop/Quant Finance/Code/BlackBoxes")
    print(f"Current working directory: {os.getcwd()}")

    # Constants
    DATA_FOLDER = "/Users/niccolo/Desktop/Quant Finance/Code/Returns_and_Backtest/FOREX/Algo_Trading/data/2y_1h_OHLC_FOREX"
    INITIAL_CAPITAL = 100000
    COMMISSION = 0.0001
    RISK_FREE_RATE = 0.02

    # Create a timestamp for the results folder
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    results_folder = f"results_{timestamp}"
    results_folder_path = os.path.abspath(results_folder)
    os.makedirs(results_folder_path, exist_ok=True)
    print(f"Results folder path: {results_folder_path}")

    # Parameter ranges
    param_ranges = {
        'position_size': np.arange(0.1, 1.0, 0.5),
        'atr_period': range(3, 15, 6),
        'high_period': range(3, 15, 6),
        'lower_band_multiplier': np.arange(1.5, 3.0, 1),
        'upper_band_multiplier': np.arange(1.5, 3.0, 1),
        'long_size': np.arange(0.2, 1.0, 0.4),
        'short_size': np.arange(0.2, 1.0, 0.4)
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

        # Split the data into train (3/4) and test (1/4) sets
        train_data, test_data = split_data(data, train_ratio=0.75)

        # Change this line to use results_folder_path instead of DATA_FOLDER
        currency_folder = os.path.join(results_folder_path, os.path.basename(CURRENCY_PAIR))
        os.makedirs(currency_folder, exist_ok=True)
        print(f"Currency folder path: {currency_folder}")

        for target in optimization_targets:
            print(f"\nOptimizing for {target}")
            
            # Perform walk-forward optimization
            wfo_results, best_params_list = walk_forward_optimization(train_data, param_ranges, target, train_ratio=0.6, test_ratio=0.2)
            
            # Debug: Print the first few results
            print("Debug: First few WFO results:")
            for result in wfo_results[:3]:
                print(f"Start: {result['start_date']}, End: {result['end_date']}")
                print(f"Best params: {result['best_params']}")
                print(f"Train metric: {result['train_metric']}, Test metric: {result['test_metric']}")
                print("---")
            
            # Generate and save heatmaps
            plot_heatmaps(wfo_results, param_ranges, target, currency_folder)
            
            # Aggregate walk-forward optimization results
            best_params, avg_train_metric, avg_test_metric = aggregate_walk_forward_results(wfo_results)

            print(f"Debug: Aggregated best parameters: {best_params}")
            print(f"Debug: Average train metric: {avg_train_metric}")
            print(f"Debug: Average test metric: {avg_test_metric}")

            # Flatten the nested dictionary if necessary
            if 'position_size' in best_params and isinstance(best_params['position_size'], dict):
                best_params = {**best_params, **best_params.pop('position_size')}

            print(f"Debug: Final best parameters for backtest: {best_params}")

            # Run backtest on test data with best parameters
            bt_results = run_single_backtest(test_data, best_params, cash=INITIAL_CAPITAL, commission=COMMISSION)

            print(f"Backtest results: {bt_results}")

            equity_curve = bt_results['_equity_curve']['Equity'].values
            annualized_return = calculate_annualized_return(equity_curve)
            max_drawdown = calculate_max_drawdown(equity_curve)
            sharpe_ratio = calculate_sharpe_ratio(equity_curve, RISK_FREE_RATE)
            sortino_ratio = calculate_sortino_ratio(equity_curve, RISK_FREE_RATE)

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

            # Calculate buy and hold equity curve
            buy_hold_equity = INITIAL_CAPITAL * (1 + test_data['Close'].pct_change().cumsum())

            # Plot equity curves comparison
            plot_equity_curves(equity_curve, buy_hold_equity, test_data, CURRENCY_PAIR, currency_folder)

            # Save results for this currency pair and optimization target
            target_folder = os.path.join(currency_folder, f"{target}_optimization")
            os.makedirs(target_folder, exist_ok=True)
            
            result_df = pd.DataFrame([result])
            result_df.to_csv(os.path.join(target_folder, f'optimization_results_{target}.csv'), index=False)

        # Add to top performers list
        top_performers.append({
            'currency_pair': CURRENCY_PAIR,
            'end_equity': equity_curve[-1]
        })

    # Calculate and print summary statistics
    summary_stats = {}
    for target in optimization_targets:
        df = pd.DataFrame(all_results[target])
        
        numeric_columns = df.select_dtypes(include=[np.number]).columns
        non_numeric_columns = df.select_dtypes(exclude=[np.number]).columns

        mean_params = df[numeric_columns].mean()
        std_params = df[numeric_columns].std()
        
        if 'final_test_annualized_return' in mean_params and 'final_test_annualized_return' in std_params:
            lowest_feasible_return = mean_params['final_test_annualized_return'] - 3 * std_params['final_test_annualized_return']
        else:
            lowest_feasible_return = None
            print(f"Warning: 'final_test_annualized_return' not found in results for {target}")
        
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
    summary_df.to_csv(os.path.join(results_folder_path, 'summary_statistics.csv'), index=False)

    # Sort and print top 5 performers
    top_performers.sort(key=lambda x: x['end_equity'], reverse=True)
    print("\nTop 5 Performers (Optimized End Equity):")
    for i, performer in enumerate(top_performers[:5], 1):
        print(f"{i}. {performer['currency_pair']}: ${performer['end_equity']:,.2f}")

    # Save top 5 performers to CSV
    top_performers_df = pd.DataFrame(top_performers[:5])
    top_performers_df.to_csv(os.path.join(results_folder_path, 'top_5_performers.csv'), index=False)

    print(f"\nAll results, summary statistics, and top performers have been saved in the '{results_folder_path}' directory.")

if __name__ == "__main__":
    main()
