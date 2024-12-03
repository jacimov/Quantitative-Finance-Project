import yfinance as yf
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec
import datetime
import os
import logging
from typing import Dict, Any
from backtesting import Backtest, Strategy
from strategy_comparison import (
    KeltnerChannelStrategy,
    LongShortStrategy,
    optimize_strategy,
    set_professional_style,
    plot_keltner_strategy,
    plot_longshort_strategy,
    plot_equity_curves,
    create_performance_table
)

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def fetch_optimization_data(ticker: str = 'EURUSD=X') -> pd.DataFrame:
    """
    Fetch 1-hour data for optimization, excluding the last week
    """
    try:
        end_date = datetime.datetime.now().date() - datetime.timedelta(days=7)  # A week ago
        start_date = end_date - datetime.timedelta(days=365)  # One year of data
        
        logger.info(f"Fetching optimization data for {ticker} from {start_date} to {end_date}")
        data = yf.download(ticker, start=start_date, end=end_date, interval='1h', progress=False)
        
        if data.empty:
            raise ValueError(f"No optimization data retrieved for {ticker}")
            
        logger.info(f"Successfully retrieved {len(data)} optimization data points")
        return data
        
    except Exception as e:
        logger.error(f"Error fetching optimization data: {str(e)}")
        raise

def fetch_evaluation_data(ticker: str = 'EURUSD=X') -> pd.DataFrame:
    """
    Fetch 1-minute data for the last week for evaluation
    """
    try:
        end_date = datetime.datetime.now().date() - datetime.timedelta(days=1)  # Yesterday
        start_date = end_date - datetime.timedelta(days=7)  # Last week of data
        
        logger.info(f"Fetching minute evaluation data for {ticker} from {start_date} to {end_date}")
        data = yf.download(ticker, start=start_date, end=end_date, interval='1m', progress=False)
        
        if data.empty:
            raise ValueError(f"No minute evaluation data retrieved for {ticker}")
            
        logger.info(f"Successfully retrieved {len(data)} minute evaluation data points")
        return data
        
    except Exception as e:
        logger.error(f"Error fetching minute evaluation data: {str(e)}")
        raise

def optimize_and_evaluate(
    ticker: str = 'EURUSD=X',
    plot_strategies: bool = True,
    cash: float = 10000,
    commission: float = 0.002
) -> None:
    """
    Two-step process:
    1. Optimize strategies on 1-hour historical data
    2. Evaluate optimized strategies on recent 1-minute data
    """
    # Set professional plotting style
    colors = set_professional_style()
    
    # Step 1: Optimization on 1-hour data
    logger.info("Starting optimization phase...")
    optimization_data = fetch_optimization_data(ticker)
    
    # Optimization parameter ranges
    keltner_param_ranges = {
        'n': [10, 20, 30],
        'atr_period': [10, 14, 20],
        'multiplier': [1.5, 2.0, 2.5]
    }
    
    longshort_param_ranges = {
        'n': [10, 20, 30],
        'multiplier': [1.5, 2.0, 2.5]
    }
    
    # Optimize both strategies
    keltner_params = optimize_strategy(KeltnerChannelStrategy, optimization_data, keltner_param_ranges, cash, commission)
    longshort_params = optimize_strategy(LongShortStrategy, optimization_data, longshort_param_ranges, cash, commission)
    
    logger.info(f"Optimized Keltner parameters: {keltner_params}")
    logger.info(f"Optimized Long-Short parameters: {longshort_params}")
    
    # Step 2: Evaluation on minute data
    logger.info("Starting evaluation phase...")
    evaluation_data = fetch_evaluation_data(ticker)
    
    # Run backtests with optimized parameters
    keltner_bt = Backtest(evaluation_data, KeltnerChannelStrategy, cash=cash, commission=commission)
    longshort_bt = Backtest(evaluation_data, LongShortStrategy, cash=cash, commission=commission)
    
    # Set optimized parameters
    for name, value in keltner_params.items():
        setattr(KeltnerChannelStrategy, name, value)
    for name, value in longshort_params.items():
        setattr(LongShortStrategy, name, value)
    
    # Run strategies
    keltner_stats = keltner_bt.run()
    longshort_stats = longshort_bt.run()
    
    if plot_strategies:
        # Create figure with custom layout
        fig = plt.figure(figsize=(15, 10))
        
        # Add main title for the entire figure
        fig.suptitle(f'Strategy Comparison: {evaluation_data.index[0].strftime("%Y-%m-%d")}-{evaluation_data.index[-1].strftime("%Y-%m-%d")}\n' + 
                    'Optimized on 1h Data, Evaluated on 1m Data', 
                    fontsize=14, fontweight='bold', y=0.95)
        
        # Create a more complex grid
        gs = GridSpec(2, 2, figure=fig, width_ratios=[1, 1], height_ratios=[1, 1])
        
        # Left column: Stacked strategy plots
        ax1 = fig.add_subplot(gs[0, 0])  # Top left: Keltner
        plot_keltner_strategy(evaluation_data, keltner_params, ax1, colors)
        ax1.set_title('Keltner Channel Strategy', pad=10)
        
        ax2 = fig.add_subplot(gs[1, 0])  # Bottom left: Long-Short
        plot_longshort_strategy(evaluation_data, longshort_params, ax2, colors)
        ax2.set_title('Long-Short Strategy', pad=10)
        
        # Right column
        ax3 = fig.add_subplot(gs[0, 1])  # Top right: Equity curves
        plot_equity_curves(keltner_stats, longshort_stats, ax3, colors)
        
        ax4 = fig.add_subplot(gs[1, 1])  # Bottom right: Performance table
        create_performance_table(keltner_stats, longshort_stats, ax4, colors)
        
        # Adjust layout to accommodate the main title
        plt.tight_layout(rect=[0, 0, 1, 0.95])
        
        # Save figure to desktop with timestamp
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        desktop = os.path.expanduser("~/Desktop")
        filename = os.path.join(desktop, f'strategy_evaluation_1m_{timestamp}.png')
        plt.savefig(filename, dpi=300, bbox_inches='tight')
        logger.info(f"Minute evaluation plot saved as {filename}")
        
        # Close figure to free memory
        plt.close(fig)

if __name__ == "__main__":
    optimize_and_evaluate()
