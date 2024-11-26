"""
Visualization Module

This module provides visualization tools
for analyzing trading strategy performance
and parameter optimization results. It includes functionality for creating:
1. Parameter optimization heatmaps
2. Equity curve comparisons
3. Price charts

The visualizations help in:
- Understanding parameter interactions
- Evaluating strategy performance
- Comparing strategy returns to benchmark
- Analyzing price movements
"""

import matplotlib.pyplot as plt
import numpy as np
import os
import pandas as pd
from itertools import combinations


def plot_heatmaps(
    wfo_results,
    param_ranges,
    optimization_target,
    currency_folder
):
    """
    Create and save heatmaps showing parameter optimization results.

    This function generates heatmaps that visualize the relationships between
    different strategy parameters and their impact on the optimization target.
    It helps identify optimal parameter combinations and understand parameter
    interactions.

    Args:
        wfo_results (list): Results from walk-forward optimization
        param_ranges (dict): Dictionary of parameter ranges tested
        optimization_target (str): Metric being optimized
        currency_folder (str): Directory to save the heatmap plots

    Note:
        Heatmaps are saved as PNG files in the specified currency_folder
    """
    print(f"plot_heatmaps: Received currency_folder: {currency_folder}")
    os.makedirs(currency_folder, exist_ok=True)

    # Extract all parameter combinations and their corresponding metrics
    all_params = []
    all_metrics = []
    for result in wfo_results:
        all_params.append(result['best_params'])
        all_metrics.append(result['train_metric'])

    df = pd.DataFrame(all_params)
    df[optimization_target] = all_metrics

    heatmap_params = [
        'position_size',
        'lower_band_multiplier',
        'upper_band_multiplier',
        'long_size',
        'short_size'
    ]
    heatmap_params = [param for param in heatmap_params if param in df.columns]

    param_pairs = list(combinations(heatmap_params, 2))

    if not param_pairs:
        print("Error: No parameter pairs available for heatmap plotting.")
        return

    n_plots = len(param_pairs)
    n_cols = min(2, n_plots)
    n_rows = (n_plots + 1) // 2
    fig, axs = plt.subplots(n_rows, n_cols, figsize=(20, 10 * n_rows))
    title = (
        f'Parameter Optimization Heatmaps - '
        f'{optimization_target.capitalize()}'
    )
    fig.suptitle(title, fontsize=16, y=1.02)

    if n_plots == 1:
        axs = np.array([[axs]])
    elif n_rows == 1:
        axs = axs.reshape(1, -1)

    for idx, (param1, param2) in enumerate(param_pairs):
        row = idx // n_cols
        col = idx % n_cols
        ax = axs[row, col]

        pivot = df.pivot_table(
            values=optimization_target,
            index=param1,
            columns=param2,
            aggfunc='mean'
        )

        im = ax.imshow(
            pivot,
            cmap='YlOrRd',
            aspect='auto',
            interpolation='nearest'
        )
        ax.set_title(f'{param1} vs {param2}')
        ax.set_xlabel(param2)
        ax.set_ylabel(param1)

        ax.set_xticks(np.arange(len(pivot.columns)))
        ax.set_yticks(np.arange(len(pivot.index)))
        ax.set_xticklabels(pivot.columns)
        ax.set_yticklabels(pivot.index)

        plt.setp(
            ax.get_xticklabels(),
            rotation=45,
            ha="right",
            rotation_mode="anchor"
        )

        fig.colorbar(im, ax=ax)

    for idx in range(n_plots, n_rows * n_cols):
        fig.delaxes(axs.flatten()[idx])

    plt.tight_layout(rect=[0, 0.03, 1, 0.95])
    save_path = os.path.join(
        currency_folder,
        f"parameter_heatmaps_{optimization_target}.png"
    )
    plt.savefig(save_path, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"Heatmap saved to: {save_path}")


def plot_equity_curves(
    optimized_equity,
    buy_hold_equity,
    forex_data,
    currency_pair,
    currency_folder
):
    """
    Create and save plots comparing strategy equity curves and forex prices.

    This function generates two subplots:
    1. Comparison of optimized strategy equity curve vs buy-and-hold
    2. Underlying forex price movement

    Args:
        optimized_equity (array-like): Equity curve of the optimized strategy
        buy_hold_equity (array-like): Equity curve of buy-and-hold strategy
        forex_data (pd.DataFrame): Historical forex price data
        currency_pair (str): Name of the forex pair being analyzed
        currency_folder (str): Directory to save the plots

    Note:
        Plots are saved as PNG files in the specified currency_folder
    """
    print(f"plot_equity_curves: Received currency_folder: {currency_folder}")
    os.makedirs(currency_folder, exist_ok=True)

    if isinstance(optimized_equity, np.ndarray):
        optimized_equity = pd.Series(optimized_equity)
    if isinstance(buy_hold_equity, np.ndarray):
        buy_hold_equity = pd.Series(buy_hold_equity)

    equity_index = pd.date_range(
        end=forex_data.index[-1],
        periods=len(optimized_equity),
        freq='h'
    )

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 10), sharex=True)

    ax1.plot(equity_index, optimized_equity, label='Optimized Strategy')
    ax1.plot(equity_index, buy_hold_equity, label='Buy and Hold')
    ax1.set_title(f'Equity Curve Comparison - {currency_pair}')
    ax1.set_ylabel('Equity')
    ax1.legend()
    ax1.grid(True)

    ax2.plot(
        forex_data.index,
        forex_data['Close'],
        label='Forex Price',
        color='green'
    )
    ax2.set_title(f'Forex Price - {currency_pair}')
    ax2.set_xlabel('Time')
    ax2.set_ylabel('Price')
    ax2.legend()
    ax2.grid(True)

    plt.tight_layout()

    safe_currency_pair = ''.join(
        c for c in currency_pair if c.isalnum() or c in ('_', '-')
    )

    save_path = os.path.join(
        currency_folder,
        f"equity_and_price_comparison_{safe_currency_pair}.png"
    )
    plt.savefig(save_path, dpi=300, bbox_inches='tight')
    plt.close()
