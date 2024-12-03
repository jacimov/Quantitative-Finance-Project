import pandas as pd
import numpy as np
import yfinance as yf
import matplotlib.pyplot as plt
from backtesting import Backtest, Strategy
from backtesting.lib import crossover
import itertools
from tqdm import tqdm
import logging
from typing import Dict, Any, List
import seaborn as sns
import matplotlib.dates as mdates
from matplotlib.gridspec import GridSpec
import os
import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

class KeltnerChannelStrategy(Strategy):
    """
    Keltner Channel trading strategy with optimizable parameters
    """
    def init(self):
        # Strategy parameters with default values
        if not hasattr(self, 'n'):
            self.n = 20
        if not hasattr(self, 'atr_period'):
            self.atr_period = 14
        if not hasattr(self, 'multiplier'):
            self.multiplier = 2.0

        def custom_ema(data, period):
            """Calculate Exponential Moving Average"""
            alpha = 2 / (period + 1)
            ema = np.zeros_like(data)
            ema[0] = data[0]
            for i in range(1, len(data)):
                ema[i] = alpha * data[i] + (1 - alpha) * ema[i-1]
            return ema
        
        def custom_std(data, period):
            """Calculate Standard Deviation"""
            std = np.zeros_like(data)
            for i in range(period-1, len(data)):
                std[i] = np.std(data[i-period+1:i+1])
            return std
        
        # Calculate indicators
        self.ema = self.I(custom_ema, self.data.Close, self.n)
        self.std = self.I(custom_std, self.data.Close, self.atr_period)
        self.upper = self.ema + self.std * self.multiplier
        self.lower = self.ema - self.std * self.multiplier

    def next(self):
        if self.position:
            if self.data.Close[-1] > self.upper[-1]:
                self.position.close()
        else:
            if self.data.Close[-1] < self.lower[-1]:
                self.buy()

class LongShortStrategy(Strategy):
    """
    Long-Short trading strategy with optimizable parameters
    """
    def init(self):
        # Strategy parameters with default values
        if not hasattr(self, 'n'):
            self.n = 20
        if not hasattr(self, 'multiplier'):
            self.multiplier = 2.0

        def custom_sma(data, period):
            """Calculate Simple Moving Average"""
            sma = np.zeros_like(data)
            for i in range(period-1, len(data)):
                sma[i] = np.mean(data[i-period+1:i+1])
            return sma
        
        def custom_std(data, period):
            """Calculate Standard Deviation"""
            std = np.zeros_like(data)
            for i in range(period-1, len(data)):
                std[i] = np.std(data[i-period+1:i+1])
            return std
        
        # Calculate indicators
        self.rolling_mean = self.I(custom_sma, self.data.Close, self.n)
        self.std = self.I(custom_std, self.data.Close, self.n)
        self.upper = self.rolling_mean + self.std * self.multiplier
        self.lower = self.rolling_mean - self.std * self.multiplier

    def next(self):
        if self.position:
            if self.position.is_long and self.data.Close[-1] > self.upper[-1]:
                self.position.close()
            elif self.position.is_short and self.data.Close[-1] < self.lower[-1]:
                self.position.close()
        else:
            if self.data.Close[-1] < self.lower[-1]:
                self.buy()
            elif self.data.Close[-1] > self.upper[-1]:
                self.sell()

def optimize_strategy(
    strategy_class: type, 
    data: pd.DataFrame, 
    param_ranges: dict,
    cash: float = 10000, 
    commission: float = 0.002
) -> dict:
    """
    Optimize strategy parameters using grid search
    """
    best_sharpe = float('-inf')
    best_params = None
    total_combinations = np.prod([len(values) for values in param_ranges.values()])
    
    logger.info(f"Total parameter combinations: {total_combinations}")
    
    # Create parameter combinations
    param_names = list(param_ranges.keys())
    param_values = list(param_ranges.values())
    combinations = list(itertools.product(*param_values))
    
    # Progress bar for optimization
    with tqdm(total=total_combinations, desc=f"Optimizing {strategy_class.__name__}") as pbar:
        for combo in combinations:
            params = dict(zip(param_names, combo))
            
            try:
                # Create strategy instance with parameters
                strategy = strategy_class
                for name, value in params.items():
                    setattr(strategy, name, value)
                
                # Run backtest
                bt = Backtest(data, strategy, cash=cash, commission=commission)
                stats = bt.run()
                
                # Update best parameters if sharpe ratio is better
                if stats['Sharpe Ratio'] > best_sharpe:
                    best_sharpe = stats['Sharpe Ratio']
                    best_params = params
                    logger.info(f"New best parameters found: {params} with Sharpe Ratio: {best_sharpe}")
                
            except Exception as e:
                logger.warning(f"Error with parameters {params}: {str(e)}")
            
            pbar.update(1)
    
    if best_params is None:
        logger.warning("No valid parameters found during optimization")
        # Return middle values from parameter ranges as default
        best_params = {k: v[len(v)//2] for k, v in param_ranges.items()}
        
    return best_params

def walk_forward_optimization(
    ticker: str = 'EURUSD=X', 
    train_ratio: float = 0.8,
    plot_strategies: bool = True
):
    """
    Perform walk-forward optimization and backtesting with enhanced visualization and analysis
    """
    # Set professional plotting style
    colors = set_professional_style()
    
    # Calculate date range dynamically
    end_date = datetime.datetime.now().date() - datetime.timedelta(days=1)  # Yesterday
    start_date = end_date - datetime.timedelta(days=365)  # One year before
    
    logger.info(f"Fetching data for {ticker} from {start_date} to {end_date}")
    data = yf.download(ticker, start=start_date, end=end_date, interval='1h', progress=False)
    
    if data.empty:
        logger.error("No data downloaded. Please check the ticker and date range.")
        return
    
    # Prepare the data
    data.index = pd.to_datetime(data.index)
    data = data.dropna()
    
    # Split data into training and testing sets
    split_idx = int(len(data) * train_ratio)
    train_data = data[:split_idx]
    test_data = data[split_idx:]
    
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
    
    # Optimize strategies
    logger.info("Starting optimization for KeltnerChannelStrategy")
    keltner_params = optimize_strategy(KeltnerChannelStrategy, train_data, keltner_param_ranges)
    logger.info(f"Best parameters for Keltner: {keltner_params}")
    
    logger.info("Starting optimization for LongShortStrategy")
    longshort_params = optimize_strategy(LongShortStrategy, train_data, longshort_param_ranges)
    logger.info(f"Best parameters for Long-Short: {longshort_params}")
    
    # Create strategy instances with optimized parameters
    keltner_strategy = KeltnerChannelStrategy
    for name, value in keltner_params.items():
        setattr(keltner_strategy, name, value)
        
    longshort_strategy = LongShortStrategy
    for name, value in longshort_params.items():
        setattr(longshort_strategy, name, value)
    
    # Run backtests with optimized parameters
    keltner_bt = Backtest(test_data, keltner_strategy, cash=10000, commission=0.002)
    longshort_bt = Backtest(test_data, longshort_strategy, cash=10000, commission=0.002)
    
    keltner_stats = keltner_bt.run()
    longshort_stats = longshort_bt.run()
    
    if plot_strategies:
        # Create figure with custom layout
        fig = plt.figure(figsize=(15, 10))
        
        # Add main title for the entire figure
        fig.suptitle(f'Strategy Comparison: {ticker.replace("=X", "")} Currency Pair', 
                    fontsize=14, fontweight='bold', y=0.95)
        
        # Create a more complex grid
        gs = GridSpec(2, 2, figure=fig, width_ratios=[1, 1], height_ratios=[1, 1])
        
        # Left column: Stacked strategy plots
        ax1 = fig.add_subplot(gs[0, 0])  # Top left: Keltner
        plot_keltner_strategy(test_data, keltner_params, ax1, colors)
        ax1.set_title('Keltner Channel Strategy', pad=10)
        
        ax2 = fig.add_subplot(gs[1, 0])  # Bottom left: Long-Short
        plot_longshort_strategy(test_data, longshort_params, ax2, colors)
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
        save_path = os.path.expanduser(f"~/Desktop/strategy_comparison_{ticker}_{timestamp}.png")
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        logger.info(f"Figure saved to: {save_path}")
        
        plt.show()
    
    return {
        'keltner_stats': keltner_stats,
        'longshort_stats': longshort_stats,
        'keltner_params': keltner_params,
        'longshort_params': longshort_params
    }

def set_professional_style():
    """Set professional plotting style for matplotlib"""
    plt.style.use('default')
    
    # Color palette
    colors = {
        'blue': '#2878B5',
        'red': '#C82423',
        'green': '#009872',
        'orange': '#F39200',
        'purple': '#542437',
        'gray': '#808080'
    }
    
    # Style parameters
    plt.rcParams.update({
        'figure.facecolor': 'white',
        'axes.facecolor': 'white',
        'axes.grid': True,
        'grid.color': '#E6E6E6',
        'grid.linestyle': '-',
        'grid.alpha': 0.5,
        'font.family': 'sans-serif',
        'font.size': 10,
        'axes.labelsize': 11,
        'axes.titlesize': 12,
        'xtick.labelsize': 10,
        'ytick.labelsize': 10,
        'legend.fontsize': 10,
        'lines.linewidth': 1.5
    })
    
    return colors

def plot_keltner_strategy(data, params, ax, colors):
    """Enhanced plotting for Keltner Channel Strategy"""
    # Calculate indicators
    n = params['n']
    multiplier = params['multiplier']
    atr_period = params['atr_period']
    
    # Calculate EMA
    ema = data.Close.ewm(span=n, adjust=False).mean()
    
    # Calculate ATR-based bands
    high_low = data['High'] - data['Low']
    high_close = np.abs(data['High'] - data['Close'].shift())
    low_close = np.abs(data['Low'] - data['Close'].shift())
    ranges = pd.concat([high_low, high_close, low_close], axis=1)
    true_range = ranges.max(axis=1)
    atr = true_range.rolling(window=atr_period).mean()
    
    upper = ema + (multiplier * atr)
    lower = ema - (multiplier * atr)
    
    # Plot price and bands
    ax.plot(data.index, data.Close, color=colors['gray'], label='Price', alpha=0.7)
    ax.plot(data.index, ema, color=colors['blue'], label='EMA', linewidth=1)
    ax.plot(data.index, upper, '--', color=colors['red'], label='Upper Band', alpha=0.7)
    ax.plot(data.index, lower, '--', color=colors['green'], label='Lower Band', alpha=0.7)
    
    ax.legend(loc='upper left', frameon=True, fancybox=True, framealpha=0.9)
    ax.set_xlabel('Date')
    ax.set_ylabel('Price')
    plt.setp(ax.get_xticklabels(), rotation=45, ha='right')

def plot_longshort_strategy(data, params, ax, colors):
    """Enhanced plotting for Long-Short Strategy"""
    # Calculate indicators
    n = params['n']
    multiplier = params['multiplier']
    
    # Calculate rolling mean and std
    rolling_mean = data.Close.rolling(window=n).mean()
    rolling_std = data.Close.rolling(window=n).std()
    
    upper = rolling_mean + (multiplier * rolling_std)
    lower = rolling_mean - (multiplier * rolling_std)
    
    # Plot price and bands
    ax.plot(data.index, data.Close, color=colors['gray'], label='Price', alpha=0.7)
    ax.plot(data.index, rolling_mean, color=colors['blue'], label='Mean', linewidth=1)
    ax.plot(data.index, upper, '--', color=colors['red'], label='Upper Band', alpha=0.7)
    ax.plot(data.index, lower, '--', color=colors['green'], label='Lower Band', alpha=0.7)
    
    ax.legend(loc='upper left', frameon=True, fancybox=True, framealpha=0.9)
    ax.set_xlabel('Date')
    ax.set_ylabel('Price')
    plt.setp(ax.get_xticklabels(), rotation=45, ha='right')

def plot_equity_curves(keltner_stats, longshort_stats, ax, colors):
    """Plot equity curves for both strategies"""
    # Extract equity curves
    keltner_equity = keltner_stats._equity_curve['Equity']
    longshort_equity = longshort_stats._equity_curve['Equity']
    
    # Plot equity curves
    ax.plot(keltner_equity.index, keltner_equity, 
            label='Keltner Channel Strategy', color=colors['blue'], alpha=0.8)
    ax.plot(longshort_equity.index, longshort_equity,
            label='Long-Short Strategy', color=colors['red'], alpha=0.8)
    
    # Add baseline
    ax.axhline(y=10000, color=colors['gray'], linestyle='--', alpha=0.5, label='Initial Capital')
    
    ax.set_title('Strategy Performance Comparison', pad=10)
    ax.set_xlabel('Date')
    ax.set_ylabel('Equity')
    ax.legend(loc='upper left', frameon=True, fancybox=True, framealpha=0.9)
    
    # Format x-axis dates
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
    plt.setp(ax.get_xticklabels(), rotation=45, ha='right')

def create_performance_table(keltner_stats, longshort_stats, ax, colors):
    """Create a professional-looking performance metrics table"""
    ax.axis('off')
    
    # Define metrics to display
    metrics = {
        'Total Return': lambda x: f"{x['Return [%]']:.2f}%",
        'Sharpe Ratio': lambda x: f"{x['Sharpe Ratio']:.2f}",
        'Max Drawdown': lambda x: f"{x['Max. Drawdown [%]']:.2f}%",
        'Win Rate': lambda x: f"{x['Win Rate [%]']:.2f}%",
        'Total Trades': lambda x: f"{x['# Trades']}",
        'Profit Factor': lambda x: f"{x['Profit Factor']:.2f}",
        'Avg Trade': lambda x: f"${x['Avg. Trade']:.2f}",
        'Exposure Time': lambda x: f"{x['Exposure Time [%]']:.1f}%"
    }
    
    # Create table data
    table_data = []
    for metric_name, metric_func in metrics.items():
        try:
            keltner_value = metric_func(keltner_stats)
            longshort_value = metric_func(longshort_stats)
            table_data.append([metric_name, keltner_value, longshort_value])
        except KeyError:
            continue
    
    # Create table
    table = ax.table(
        cellText=[['Metric', 'Keltner Channel', 'Long-Short']] + table_data,
        loc='center',
        cellLoc='center',
        colWidths=[0.3, 0.35, 0.35]
    )
    
    # Style the table
    table.auto_set_font_size(False)
    table.set_fontsize(9)
    table.scale(1.2, 1.8)
    
    # Color header and alternate rows
    for i in range(len(table_data) + 1):
        for j in range(3):
            cell = table[(i, j)]
            if i == 0:  # Header
                cell.set_facecolor('#f0f0f0')
                cell.set_text_props(weight='bold')
            elif i % 2:  # Alternate rows
                cell.set_facecolor('#f9f9f9')
            
            # Add borders
            cell.set_edgecolor('#d0d0d0')
            cell.set_linewidth(0.5)
            
            # Align text
            if j == 0:  # Metric names
                cell.set_text_props(ha='left')
                cell._text.set_x(0.05)  # Add padding

if __name__ == "__main__":
    # Run walk-forward optimization and backtesting
    walk_forward_optimization()
