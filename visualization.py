# visualization.py
import matplotlib.pyplot as plt
import numpy as np
import os
from itertools import combinations
import pandas as pd

def plot_heatmaps(wfo_results, param_ranges, optimization_target, currency_folder):
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
    
    heatmap_params = ['position_size', 'lower_band_multiplier', 'upper_band_multiplier', 'long_size', 'short_size']
    heatmap_params = [param for param in heatmap_params if param in df.columns]
    
    param_pairs = list(combinations(heatmap_params, 2))
    
    if not param_pairs:
        print("Error: No parameter pairs available for heatmap plotting.")
        return
    
    n_plots = len(param_pairs)
    n_cols = min(2, n_plots)
    n_rows = (n_plots + 1) // 2
    fig, axs = plt.subplots(n_rows, n_cols, figsize=(20, 10 * n_rows))
    fig.suptitle(f'Parameter Optimization Heatmaps - {optimization_target.capitalize()}', fontsize=16)
    
    if n_plots == 1:
        axs = np.array([[axs]])
    elif n_rows == 1:
        axs = axs.reshape(1, -1)
    
    for idx, (param1, param2) in enumerate(param_pairs):
        row = idx // n_cols
        col = idx % n_cols
        ax = axs[row, col]
        
        pivot = df.pivot_table(values=optimization_target, 
                               index=param1, 
                               columns=param2, 
                               aggfunc='mean')
        
        im = ax.imshow(pivot, cmap='YlOrRd', aspect='auto', interpolation='nearest')
        ax.set_title(f'{param1} vs {param2}')
        ax.set_xlabel(param2)
        ax.set_ylabel(param1)
        
        ax.set_xticks(np.arange(len(pivot.columns)))
        ax.set_yticks(np.arange(len(pivot.index)))
        ax.set_xticklabels(pivot.columns)
        ax.set_yticklabels(pivot.index)
        
        plt.setp(ax.get_xticklabels(), rotation=45, ha="right", rotation_mode="anchor")
        
        fig.colorbar(im, ax=ax)
    
    for idx in range(n_plots, n_rows * n_cols):
        fig.delaxes(axs.flatten()[idx])
    
    plt.tight_layout(rect=[0, 0.03, 1, 0.95])
    save_path = os.path.join(currency_folder, f"parameter_heatmaps_{optimization_target}.png")
    plt.savefig(save_path, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"Heatmap saved to: {save_path}")

def plot_equity_curves(optimized_equity, buy_hold_equity, forex_data, currency_pair, currency_folder):
    print(f"plot_equity_curves: Received currency_folder: {currency_folder}")
    os.makedirs(currency_folder, exist_ok=True)
    
    if isinstance(optimized_equity, np.ndarray):
        optimized_equity = pd.Series(optimized_equity)
    if isinstance(buy_hold_equity, np.ndarray):
        buy_hold_equity = pd.Series(buy_hold_equity)
    
    equity_index = pd.date_range(end=forex_data.index[-1], periods=len(optimized_equity), freq='h')
    
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 10), sharex=True)
    
    ax1.plot(equity_index, optimized_equity, label='Optimized Strategy')
    ax1.plot(equity_index, buy_hold_equity, label='Buy and Hold')
    ax1.set_title(f'Equity Curve Comparison - {currency_pair}')
    ax1.set_ylabel('Equity')
    ax1.legend()
    ax1.grid(True)
    
    ax2.plot(forex_data.index, forex_data['Close'], label='Forex Price', color='green')
    ax2.set_title(f'Forex Price - {currency_pair}')
    ax2.set_xlabel('Time')
    ax2.set_ylabel('Price')
    ax2.legend()
    ax2.grid(True)
    
    plt.tight_layout()
    
    # Sanitize the currency_pair string for use in a filename
    safe_currency_pair = ''.join(c for c in currency_pair if c.isalnum() or c in ('_', '-'))
    
    save_path = os.path.join(currency_folder, f"equity_and_price_comparison_{safe_currency_pair}.png")
    plt.savefig(save_path, dpi=300, bbox_inches='tight')
    plt.close()
